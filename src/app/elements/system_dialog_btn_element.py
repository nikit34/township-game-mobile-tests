from appium.webdriver.common.appiumby import AppiumBy

from configs.desired_caps_config import DesiredCapsConfig
from src.app.elements._multiple_base_selenium_elements import BaseSeleniumElements


class SystemDialogBtnElement(BaseSeleniumElements):
    BUTTON_LOCATOR = (AppiumBy.ID, DesiredCapsConfig.get_package_name() + ":id/system_dialog_button")

    def __init__(self, driver, index):
        super().__init__(driver, self.BUTTON_LOCATOR, index)