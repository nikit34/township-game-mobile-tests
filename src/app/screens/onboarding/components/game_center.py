from appium.webdriver.common.appiumby import AppiumBy

from src.base_elements.base_selenium_element import BaseSeleniumElement


class GameCenterComponent(BaseSeleniumElement):
    CLOSE_BTN = (AppiumBy.ACCESSIBILITY_ID, "UIA.GameCenter.SignIn.cancelButton")

    def __init__(self, driver, locator):
        super().__init__(driver, locator)
