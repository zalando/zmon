var Scenario = require('./scenarios/downtimes.scenario');
var downtimes = new Scenario();

var Auth = require('./scenarios/auth.scenario');
var auth = new Auth();

var P = protractor.getInstance();

describe('Testing downtimes', function() {

    beforeEach(function() {
        browser.get('/#/alert-details/704');
    });

    it('User should be logged in', function() {
        auth.login(function(loggedIn) {
            expect(loggedIn).toBe(true);
        });
    });

    it('checking the header checkbox for "Schedule downtimes" should check checkboxes of all entities', function() {
        downtimes.checkAllScheduleDowntimesCheckboxes(function(checkedScheduleDowntimes) {
            expect(checkedScheduleDowntimes.count()).toBe(14);
        });
    });

    it('checking the header checkbox for "Schedule downtimes" & unchecking the first checkbox for "Schedule downtimes" should reduce total checked checkboxes by one and also uncheck header checkbox', function() {
        downtimes.uncheckFirstScheduleDowntimeCheckbox(function(checkedScheduleDowntimes, checkedheaderScheduleDowntimesCheckbox) {
            expect(checkedScheduleDowntimes.count()).toBe(13);
            expect(checkedheaderScheduleDowntimesCheckbox.count()).toBe(0);
        });
    });

    it('should select all alerts using header checkbox and open the downtimes modal when the flag icon is clicked', function() {
        downtimes.openSetDowntimesModal(function() {
            expect(downtimes.setDowntimesModal.isDisplayed()).toBe(true);
        });
    });

    it('should select all alerts using header checkbox, open the downtimes modal and set downtime of 1h duration + reason', function() {
        downtimes.create1hDowntime(function() {
            expect(downtimes.downtimesTabHeader.getText()).toBe('Downtimes (14)');
        });
    });


    it('should delete all downtimes', function() {
        downtimes.deleteAllDowntimes(function() {
            expect(downtimes.downtimesTabHeader.getText()).toBe('Downtimes (0)');
        });
    });

    it('User should be logged out', function() {
        auth.logout(function(loggedOut) {
            expect(loggedOut).toBe(true);
        });
    });

});
