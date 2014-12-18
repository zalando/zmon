var P = protractor.getInstance();
var CheckDefPage = function() {};


CheckDefPage.prototype.searchForm = element(by.model('checkFilter'));

CheckDefPage.prototype.gotoCheckDef = function(CHECK_NAME){
    this.searchForm.sendKeys(CHECK_NAME);
    element(by.repeater("def in checkDefinitions").column('name')).click();
};

CheckDefPage.prototype.getCheckName = function(){
    return element(by.css('.col-md-8 .ng-binding')).getText();
}

CheckDefPage.prototype.getCheckCommand = function(){
    return element(by.css('.z-code.ng-binding')).getText();
}

CheckDefPage.prototype.getCheckEntities = function(){
    return element(by.css('.panel-body .entities')).getText();
}

CheckDefPage.prototype.getAlertsNumOfCheck = function(){
    var alertsOfCheck = element.all(by.css('.table-responsive.ng-scope tbody tr'));
    return alertsOfCheck.count();
}

CheckDefPage.prototype.goToAlertOfCheck = function(ALERT_NAME){
    var alertsOfCheck = element(by.cssContainingText('a.ng-binding', ALERT_NAME));
    alertsOfCheck.click();
}

module.exports = CheckDefPage;