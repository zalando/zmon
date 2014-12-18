var P = protractor.getInstance();
var History = function() {};

History.prototype.historyTab = element(by.css('.nav-tabs li:last-child'));

History.prototype.lastDayButton = element(by.css('.tab-pane:nth-child(3) .zmon-controls .btn'));

History.prototype.allEntries = element.all(by.repeater("entry in AlertDetailsCtrl.allHistory"));

History.prototype.showHistoryTab = function(cb) {
    this.historyTab.click().then(function() {
        cb();
    });
};

module.exports = History;