import os

from _pytest.fixtures import fixture
from appium.options.android import UiAutomator2Options
from appium.options.ios import XCUITestOptions
from appium import webdriver
from appium.webdriver.appium_service import AppiumService

from configs.appium_config import AppiumConfig
from configs.desired_caps_config import DesiredCapsConfig
from configs.waiting_config import WaitingConfig
from src.environment_manager import EnvironmentManager
from src.file_manager import FileManager


@fixture(scope='function')
def driver():
    desired_caps = DesiredCapsConfig.get_desired_caps()

    EnvironmentManager.execute_ios_callback(lambda: (
        desired_caps.update({
            'appium:usePrebuiltWDA': True,
            'appium:derivedDataPath': FileManager.get_full_path(
                os.path.expanduser("~/Library/Developer/Xcode/DerivedData/"), r"WebDriverAgent-[a-z]+"
            )
        })
    ) if FileManager.get_full_path(
        os.path.expanduser("~/Library/Developer/Xcode/DerivedData/"),
        r"WebDriverAgent-[a-z]+"
    ) else None)

    capabilities_options = EnvironmentManager.execute_platform_specific_callback(
        lambda: UiAutomator2Options(),
        lambda: XCUITestOptions(),
    ).load_capabilities(desired_caps)

    driver = webdriver.Remote('http://' + AppiumConfig.get_host() + ':' + str(AppiumConfig.get_port()), options=capabilities_options)

    implicitly_timeout = WaitingConfig.get_implicitly_timeout()
    driver.implicitly_wait(implicitly_timeout)

    yield driver
    driver.quit()


@fixture(scope='session')
def appium_service():
    service = AppiumService()
    host = AppiumConfig.get_host()
    port = AppiumConfig.get_port()
    timeout = AppiumConfig.get_timeout()

    service.start(
        args=['--address', host, '-p', str(port)],
        timeout_ms=timeout,
    )

    yield service
    service.stop()
