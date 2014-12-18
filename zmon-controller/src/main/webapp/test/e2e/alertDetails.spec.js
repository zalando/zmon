var Scenario = require('./scenarios/alertDetails.scenario');
var Auth = require('./scenarios/auth.scenario');

var alertDetails = new Scenario();
var auth = new Auth();

var P = protractor.getInstance();

describe('Testing alert details page', function() {

    beforeEach(function() {
        browser.get('/#/alert-details/704');
    });


    it('User should be logged in', function() {
        auth.login(function(loggedIn) {
            expect(loggedIn).toBe(true);
        });
    });

    it('Should show 14 countries and 1st country name should be "cd-kinshasa"', function() {
        alertDetails.checkCountryAlerts(function(allEntitiesArray, firstCountryName) {
            expect(allEntitiesArray.length).toBe(14);
            expect(firstCountryName).toBe('cd-kinshasa');
        });
    });

    it('After the OK button is clicked it should show 20 countries', function() {
        alertDetails.clickOKButton(function(allEntitiesArray) {
            expect(allEntitiesArray.length).toBe(20);
        });
    });

    it('After we type "delhi" in the search field it should show two countries and the first country name should be "in-delhi" ', function() {
        alertDetails.doDelhiSearch(function(cityNamesArray) {
            expect(cityNamesArray.length).toBe(2);
            expect(cityNamesArray[0].getText()).toBe('in-delhi');
        });
    });

    it('After clicking the "Details" toggle the details panel should become visible and "Check Command" value should be "entity[\'longitude\']"', function() {
        alertDetails.clickDetailsPanelToggle(function() {
            expect(alertDetails.detailsPanelBody.isDisplayed()).toBe(true);
            expect(alertDetails.detailsPanelCheckCommand.getText()).toBe("entity['longitude']");
        });
    });

    it('Should all details must be present', function() {
        alertDetails.checkDetails(function(details) {
            expect(details.getText()).toMatch(/ZMON2-TEST: City Longitude, ID: 20/);
            expect(details.getText()).toMatch(/Platform\/Software/);
            expect(details.getText()).toMatch(/entity\['longitude'\]/);
            expect(details.getText()).toMatch(/15s/);
            expect(details.getText()).toMatch(/type = city/);
        });
    });
});
