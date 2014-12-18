var P = protractor.getInstance();
var AlertDetails = function() {};

AlertDetails.prototype.allEntities = element.all(by.repeater("entityInstance in AlertDetailsCtrl.allAlertsAndChecks | filter:alertDetailsSearch | inDisplayedGroup:AlertDetailsCtrl.showActiveAlerts:AlertDetailsCtrl.showAlertsInDowntime:AlertDetailsCtrl.showCheckResults | orderBy:'entity' | limitTo:AlertDetailsCtrl.infScrollNumAlertsVisible"));

AlertDetails.prototype.firstCountryName = element(by.repeater("entityInstance in AlertDetailsCtrl.allAlertsAndChecks | filter:alertDetailsSearch | inDisplayedGroup:AlertDetailsCtrl.showActiveAlerts:AlertDetailsCtrl.showAlertsInDowntime:AlertDetailsCtrl.showCheckResults | orderBy:'entity' | limitTo:AlertDetailsCtrl.infScrollNumAlertsVisible").row(0).column('{{entityInstance.entity}}'));

AlertDetails.prototype.OKButton = element(by.binding('{{AlertDetailsCtrl.checkResults.length}}'));

AlertDetails.prototype.searchField = element(by.css('input.alert-details-search'));

// Get the entire column with the city names
AlertDetails.prototype.citiesColumn = element.all(by.repeater("entityInstance in AlertDetailsCtrl.allAlertsAndChecks | filter:alertDetailsSearch | inDisplayedGroup:AlertDetailsCtrl.showActiveAlerts:AlertDetailsCtrl.showAlertsInDowntime:AlertDetailsCtrl.showCheckResults | orderBy:'entity' | limitTo:AlertDetailsCtrl.infScrollNumAlertsVisible").column('{{entityInstance.entity}}'));

AlertDetails.prototype.detailsPanelToggle = element(by.css('.panel-toggle'));

AlertDetails.prototype.detailsPanelBody = element(by.css('.details .panel-body'));

AlertDetails.prototype.detailsPanelCheckCommand = element(by.binding('{{AlertDetailsCtrl.checkDefinition.command}}'));



AlertDetails.prototype.checkCountryAlerts = function(cb) {
    var that = this;
    this.allEntities.then(function(allEntitiesArray) {
        cb(allEntitiesArray, that.firstCountryName.getText());
    });
};

AlertDetails.prototype.clickOKButton = function(cb) {
    this.OKButton.click();
    this.allEntities.then(function(allEntitiesArray) {
        cb(allEntitiesArray);
    });
};

AlertDetails.prototype.doDelhiSearch = function(cb) {
    this.searchField.sendKeys('delhi');
    this.citiesColumn.then(function(cityNamesArray) {
        cb(cityNamesArray);
    });
};

AlertDetails.prototype.clickDetailsPanelToggle = function(cb) {
    this.detailsPanelToggle.click().then(cb());
};

AlertDetails.prototype.checkDetails = function(cb) {
    var that = this;
    this.detailsPanelToggle.click().then(function() {
        if(cb) cb(that.detailsPanelBody);
    });
};


module.exports = AlertDetails;
