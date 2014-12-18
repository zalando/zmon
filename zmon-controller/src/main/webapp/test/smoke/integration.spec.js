var LoginPage = require('./pageObjects/loginPage');
var Dashboard = require('./pageObjects/dashboardPage');
var CheckDefPage = require('./pageObjects/checkDefPage');
var AlertDetailPage = require('./pageObjects/alertDetailPage');
var AlertDefPage = require('./pageObjects/alertDefPage');

var loginPage = new LoginPage();
var dashboard = new Dashboard();
var checkDefPage = new CheckDefPage();
var alertDetailPage = new AlertDetailPage();
var alertDefPage = new AlertDefPage();

var P = protractor.getInstance();

var CHECK_NAME = 'ZMON2-TEST: City Longitude';
var ALERT_NAME = 'ZMON2-TEST: City Longitude >0';
var ALERT_CHANGE_NAME = 'Name after change'

describe('Smoke testing for zmon2', function() {

    it('User logged in', function() {
        loginPage.login();
    });

    it('User should see elements in dashboard', function() {
        expect(dashboard.searchForm.isDisplayed()).toBe(true);
        expect(dashboard.newDashboardButton .isDisplayed()).toBe(true);
        expect(dashboard.dashboardButton.isDisplayed()).toBe(true);
        expect(dashboard.checkDefButton.isDisplayed()).toBe(true);
        expect(dashboard.alertDefButton.isDisplayed()).toBe(true);
        expect(dashboard.reportButton.isDisplayed()).toBe(true);
        expect(dashboard.trialRunButton.isDisplayed()).toBe(true);
    });

    it('User goes to check def page', function() {
        dashboard.checkDefButton.click();
        checkDefPage.gotoCheckDef(CHECK_NAME);
        expect(checkDefPage.getCheckName()).toBe('Check: ' + CHECK_NAME);
    });

    it('Then user check the configuration of check', function(){
        expect(checkDefPage.getCheckCommand()).toBe("entity['longitude']");
        expect(checkDefPage.getCheckEntities()).toBe("type = city");
    });

    it('Then user check the alerts of check', function(){
        expect(checkDefPage.getAlertsNumOfCheck()).toBe(6);
    });

    it('Then user go to one alert of check', function(){
        checkDefPage.goToAlertOfCheck(ALERT_NAME);
        expect(alertDetailPage.getAlertName()).toBe('Alert: ' + ALERT_NAME);
    });

    it('Then user check the details of alert', function(){
        expect(alertDetailPage.getAlertCommand()).toBe("capture(foo=float(value)) > 10");
        expect(alertDetailPage.getHostList()).toBe(20);
    });

    it('Then user go to inherit page of alert', function(){
        expect(alertDetailPage.gotoInheritOfAlert()).toBe('New Alert Inheriting from: ' + ALERT_NAME);
    });

    it('Then user check inherit configuration of alert', function(){
        expect(alertDefPage.checkInheritName()).toBe(ALERT_NAME);
        expect(alertDefPage.checkInheritDesc()).toBe('Test whether a city lies east or west');
        expect(alertDefPage.checkInheritPriority()).toBe('0');
        alertDefPage.resetInheritAlertName();
    });

    it('Then user change inherit name of alert', function(){
        alertDefPage.changeInheritAlertName(ALERT_CHANGE_NAME);
        expect(alertDefPage.checkInheritName()).toBe(ALERT_CHANGE_NAME);
    });

    it('Then user reset inherit name of alert', function(){
        alertDefPage.resetInheritAlertName();
        expect(alertDefPage.checkInheritName()).toBe(ALERT_NAME);
    });

    it('User logged out', function() {
        loginPage.logout();
    });

});