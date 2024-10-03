## e2e автотесты на игру Township
в [Google Play](https://play.google.com/store/apps/details?id=com.playrix.township)

### Структура проекта
- Тесты сложены в папке `tests/` у корня репозитория
  - На втором уровне находится разделение по видам тестов (`smoke/`, `uat/`, `regress/`, `analytics/` и т.д.)
  - Названия файлов с тестами следуют шаблону `test_<цель_тестирования>.py`
- Экраны приложения расположены в папке `screens/` у корня репозитория
  - Каждый экран помещается в свою папку, даже если он там один, по принципу `screens/<НазваниеЭкранаScreen>/*.py`
  - Название экрана пишется по шаблону `<НазваниеЭкранаScreen>.py`
- Компоненты приложения могут быть размещены в двух разных местах, в зависимости от их использования:
  - Если компонент принадлежит только одному экрану, он будет помещён в папку `screens/<НазваниеЭкранаScreen>/components/*.py`
  - Если компонент встречается на разных экранах, он будет находиться в папке `components/` у корня репозитория, по принципу `components/*.py`
  - Название компонента пишется по шаблону `<НазваниеКомпонентаComponent>.py`

### Конфигурация для подключения к приложению через Appium
#### Android
```commandline
{
  "platformName": "Android",
  "appium:deviceName": "emulator-5554",
  "appium:automationName": "UiAutomator2",
  "appium:appPackage": "com.playrix.township",
  "appium:appActivity": "com.playrix.township.Launcher"
}
```