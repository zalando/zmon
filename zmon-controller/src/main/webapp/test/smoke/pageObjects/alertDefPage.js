var P = protractor.getInstance();
var AlertDefPage = function() {};

AlertDefPage.prototype.inheritName = element(by.model('alertDefinition.name'));
AlertDefPage.prototype.inheritDesc = element(by.model('alertDefinition.description'));
AlertDefPage.prototype.inheritPriority = element(by.model('alertDefinition.priority'));

AlertDefPage.prototype.checkInheritName = function(){
    return this.inheritName.getAttribute('value');
}

AlertDefPage.prototype.checkInheritDesc = function(){
    return this.inheritDesc.getAttribute('value');
}

AlertDefPage.prototype.checkInheritPriority = function(){
    return this.inheritPriority.getAttribute('value');
}

AlertDefPage.prototype.changeInheritAlertName = function(name){
    this.inheritName.clear().sendKeys(name);
}

AlertDefPage.prototype.resetInheritAlertName = function(){
    element(by.css('[ng-click="inheritProperty(\'name\')"]')).click();
}


module.exports = AlertDefPage;
