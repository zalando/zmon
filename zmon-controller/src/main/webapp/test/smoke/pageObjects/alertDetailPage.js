var P = protractor.getInstance();
var AlertDetailPage = function() {};


AlertDetailPage.prototype.getAlertName = function(){
    return element(by.css('.col-md-6')).element(by.css('.ng-binding')).getText();
}

AlertDetailPage.prototype.getAlertCommand = function(){
    return element(by.cssContainingText('.dl-horizontal', 'Condition')).element(by.css('.z-code.ng-binding')).getText();
}

AlertDetailPage.prototype.getHostList = function(){
    var alertsBtton = element.all(by.css('.col-md-8 button')).first();
    var okButton = element.all(by.css('.col-md-8 button')).last();
    okButton.getAttribute('class').then(function(t){
        if (t.indexOf('active-page') === -1) {
            okButton.click();
        }
        })
    return element.all(by.repeater('entityInstance in AlertDetailsCtrl.allAlertsAndChecks')).count();
}

AlertDetailPage.prototype.gotoInheritOfAlert = function(){
    element.all(by.css('.col-md-6.text-right a')).get(2).click();
    return element(by.css('.col-md-12 h1')).getText();
}

module.exports = AlertDetailPage;