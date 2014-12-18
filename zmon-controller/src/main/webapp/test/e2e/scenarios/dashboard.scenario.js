var P = protractor.getInstance();
var Dashboard = function() {};

Dashboard.prototype.searchForm = element(by.model('alertSearch'));

Dashboard.prototype.alertsContainer = element(by.id('zmon-alerts-container'));

Dashboard.prototype.widgetsButton = element(by.id('widgets-toggle-button'));

Dashboard.prototype.widgetsPanelLocator = by.css('.noWidgets');

Dashboard.prototype.pauseButton = element(by.css('.fa-pause'));

Dashboard.prototype.doCityLongitudeSearch = function(cb) {
    this.searchForm.clear();
    this.searchForm.sendKeys('city longitude').then(function() {
        P.findElements(by.repeater("alertInstance in alerts | filter:alertSearch | orderBy:['alert_definition.priority', '-oldestStartTime'] track by $id(alertInstance.alert_definition.id)")).then(cb);
    });
};

Dashboard.prototype.confirmRestCitiesList = function(cb) {
    P.findElements(by.repeater('entityInstance in restOfNonDowntimeEntities(alertInstance.entities)')).then(cb);
};

module.exports = Dashboard;
