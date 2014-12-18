var P = protractor.getInstance();
var TrialRun = function() {};

TrialRun.prototype.runBtn = element(by.id('run-button'));

TrialRun.prototype.stopBtn = element(by.id('stop-button'));

TrialRun.prototype.formPanel = element(by.className('form-panel'));

TrialRun.prototype.resultPanel = element(by.className('result-panel'));

TrialRun.prototype.form = element(by.id('alert-form'));

TrialRun.prototype.formLabel = element(by.css('#alert-form .form-group'));

TrialRun.prototype.iName = element(by.id('inp-name'));

TrialRun.prototype.iCommand = element(by.id('inp-command'));

TrialRun.prototype.iCondition = element(by.id('inp-condition'));

TrialRun.prototype.iEntities = element(by.id('inp-entities'));

TrialRun.prototype.iPeriod = element(by.id('inp-period'));

/*
TrialRun.prototype.clearForm = function() {
    this.iName.clear();
    this.iCommand.clear();
    this.iCondition.clear();
};
*/

TrialRun.prototype.addMinimalData = function() {
    this.iName.sendKeys('Trial run');
    this.iCommand.sendKeys('float(entity[\'longitude\'])');
    this.iCondition.sendKeys('float(value)>5');
};

/**
 * This test is excluded because we couldn't find a way to inject text in the entities filter ACE editor (divs not input)
 */
// TrialRun.prototype.submitForm = function(cb) {
//     self = this;

//     this.iName.sendKeys('Trial run');
//     this.iCommand.sendKeys('float(entity[\'longitude\'])');
//     this.iCondition.sendKeys('float(value)>5');
//     this.iEntities.click().then(function() {
//         self.iEntities.sendKeys('[{"type":"city"}]');
//         self.runBtn.click().then(function() {
//             progress = false;

//             var checkProgress = function() {
//                 element(by.className('progress-bar')).getAttribute('aria-valuenow').then(function(value) {
//                     if (!progress) {
//                         progress = (parseInt(value, 10) === 100);
//                     }
//                 });
//             };
//             P.wait(function() {
//                 checkProgress();
//                 return progress;
//             }, 60000);


//             P.findElements(by.repeater("alert in TrialRunCtrl.alerts | filter:{is_alert:true} | filter:search | orderBy:'entity.id'").column('{{alert.entity.id}}')).then(cb);
//         });
//     });
// };


module.exports = TrialRun;
