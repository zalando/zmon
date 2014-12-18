/*

Test is not reliable because of data inconsistency


var Scenario = require('./scenarios/history.scenario');
var history = new Scenario();

var P = protractor.getInstance();

describe('Testing history', function() {

    beforeEach(function() {
        browser.get('/#/alert-details/704');
    });

    it('should show history tab with 20 entries', function() {
        history.showHistoryTab(function() {
            expect(history.lastDayButton.isDisplayed()).toBe(true);
            expect(history.allEntries.count()).toBe(20);
        });
    });

});
*/