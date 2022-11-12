import logging
import time

import requests
from google.cloud.speech_v2 import SpeechClient
from google.cloud.speech_v2.types import cloud_speech
from google.oauth2 import service_account
from selenium.common import WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

logger = logging.getLogger('captcha')
handler = logging.StreamHandler()
formatter = logging.Formatter('[%(levelname)s:%(asctime)s] %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)


class GoogleTranscriber:
    def __init__(self, credentials, project_id):
        self.credentials = credentials
        self.project_id = project_id

    def _get_credentials(self):
        credentials = service_account.Credentials.from_service_account_file(
            self.credentials)
        return credentials

    def transcribe(self, content):
        client = SpeechClient(credentials=self._get_credentials())
        config = cloud_speech.RecognitionConfig(auto_decoding_config={})
        recognizer = f"projects/{self.project_id}/locations/global/recognizers/{self.project_id}"
        request = cloud_speech.RecognizeRequest(
            recognizer=recognizer, config=config, content=content)
        return ''.join(result.alternatives[0].transcript.lower()
                       for result in client.recognize(request=request).results)


class CaptchaSolver:
    def __init__(self, driver, google_service_account_credentials,
                 google_project_id,
                 delay_time=2, audio_to_text_delay=10):
        self.driver = driver
        self.delayTime = delay_time
        self.audioToTextDelay = audio_to_text_delay
        self.google_transcriber = GoogleTranscriber(
            google_service_account_credentials, google_project_id)

    def solve(self):
        logger.debug('Solving CAPTCHA ...')
        all_iframes_len = self._find_base_iframes()
        audio_btn_found, audio_btn_index = self._find_audio_button(all_iframes_len)

        if audio_btn_found:
            try:
                while True:
                    href = self.driver.find_element(By.ID, 'audio-source').get_attribute('src')
                    response = requests.get(href, stream=True)
                    text = self.google_transcriber.transcribe(response.content)
                    logger.debug(f'captcha audio: {text}')
                    self.driver.switch_to.default_content()
                    iframe = self.driver.find_elements(By.TAG_NAME, 'iframe')[audio_btn_index]
                    self.driver.switch_to.frame(iframe)
                    input_btn = self.driver.find_element(By.ID, 'audio-response')
                    input_btn.send_keys(text)
                    input_btn.send_keys(Keys.ENTER)
                    time.sleep(2)
                    error_msg = self.driver.find_elements(
                        By.CLASS_NAME, 'rc-audiochallenge-error-message')[0]
                    if error_msg.text == "" or \
                            error_msg.value_of_css_property('display') == 'none':
                        logger.debug('Success')
                        break
            except WebDriverException as e:
                if self._is_caught():
                    e.msg = 'Caught. Need to change proxy now.'
                raise e
        else:
            logger.debug('Audio button not found. CAPTCHA is already solved')

        self.driver.switch_to.default_content()

    def _find_base_iframes(self):
        try:
            google_class = self.driver.find_elements(By.CLASS_NAME, 'g-recaptcha')[0]
        except Exception as e:
            e.msg = 'There is no captcha. Maybe you are on the wrong page. ' + e.msg
            raise e

        try:
            outer_iframe = google_class.find_element(By.TAG_NAME, 'iframe')
            outer_iframe.click()
            all_iframes_len = self.driver.find_elements(By.TAG_NAME, 'iframe')
        except WebDriverException as e:
            e.msg = 'Failed to find captcha frame ' + e.msg
            raise e

        return all_iframes_len

    def _find_audio_button(self, all_iframes_len):
        audio_btn_found = False
        audio_btn_index = -1
        for index in range(len(all_iframes_len)):
            self.driver.switch_to.default_content()
            try:
                iframe = self.driver.find_elements(By.TAG_NAME, 'iframe')[index]
                self.driver.switch_to.frame(iframe)
            except WebDriverException as e:
                e.msg = 'Failed to find captcha frame 2 ' + e.msg
                raise e

            self.driver.implicitly_wait(self.delayTime)
            try:
                audio_btn = (
                        self.driver.find_element(By.ID, 'recaptcha-audio-button')
                        or self.driver.find_element(By.ID, 'recaptcha-anchor')
                )
                audio_btn.click()
                audio_btn_found = True
                audio_btn_index = index
                break
            except WebDriverException:
                pass

        return audio_btn_found, audio_btn_index

    def _is_caught(self):
        return 'Your computer or network may be sending automated queries' \
               in self.driver.page_source
