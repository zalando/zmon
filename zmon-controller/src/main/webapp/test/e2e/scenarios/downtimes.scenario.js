var P = protractor.getInstance();
var Downtimes = function() {};

// Header checkbox for scheduling downtimes
Downtimes.prototype.headerScheduleDowntimesCheckbox = element(by.id('select-all-schedule-downtimes'));

Downtimes.prototype.checkedheaderScheduleDowntimesCheckbox = element.all(by.id('.select-all-schedule-downtimes:checked'));

// All individual checkboxes for scheduling downtimes
Downtimes.prototype.checkedScheduleDowntimes = element.all(by.css('.set-downtime-checkbox:checked'));

Downtimes.prototype.setDowntimesButton = element(by.id('set-downtimes-button'));

Downtimes.prototype.setDowntimesModal = element(by.id('set-downtimes-modal'));

Downtimes.prototype.setDowntimeModalByDurationHourInput = element(by.model('hours'));

Downtimes.prototype.setDowntimeModalByDurationReasonTextarea = element(by.model('models.downtimeComment'));

Downtimes.prototype.setDowntimeModalOKButton = element(by.css('.set-downtimes-ok-button'));

Downtimes.prototype.downtimesTabHeader = element(by.css('li#downtimes-tab > a'));

Downtimes.prototype.headerDeleteDowntimesCheckbox = element(by.id('select-all-delete-downtimes'));

Downtimes.prototype.deleteDowntimesButton = element(by.id('delete-downtimes-button'));

Downtimes.prototype.checkAllScheduleDowntimesCheckboxes = function(cb) {
    var that = this;
    // Checking header checkbox for scheduling downtimes should automatically check all individual checkboxes
    this.headerScheduleDowntimesCheckbox.click().then(function() {
        cb(that.checkedScheduleDowntimes);
    });
};

Downtimes.prototype.uncheckFirstScheduleDowntimeCheckbox = function(cb) {
    var that = this;
    // Check all
    this.headerScheduleDowntimesCheckbox.click().then(function() {
        // Uncheck first
        that.checkedScheduleDowntimes.get(0).click().then(function() {
            cb(that.checkedScheduleDowntimes, that.checkedheaderScheduleDowntimesCheckbox);
        });
    });
};

Downtimes.prototype.openSetDowntimesModal = function(cb) {
    var that = this;
    // Check all
    this.headerScheduleDowntimesCheckbox.click().then(function() {
        // Open modal
        that.setDowntimesButton.click().then(cb);
    });
};

Downtimes.prototype.create1hDowntime = function(cb) {
    var that = this;
    // Check all
    this.headerScheduleDowntimesCheckbox.click().then(function() {
        // Open modal
        that.setDowntimesButton.click().then(function() {
            that.setDowntimeModalByDurationHourInput.clear();
            that.setDowntimeModalByDurationHourInput.sendKeys('1');
            that.setDowntimeModalByDurationReasonTextarea.sendKeys('reason for 1h downtime');
            that.setDowntimeModalOKButton.click().then(function() {
                var ready = false;
                P.wait(function() {
                    that.downtimesTabHeader.getText().then(function(text) {
                        if (text === 'Downtimes (14)') {
                            ready = true;
                        }
                    });
                    return ready;
                }, 20000);
                cb();
            });
        });
    });
};

Downtimes.prototype.deleteAllDowntimes = function(cb) {
    var that = this;
    this.downtimesTabHeader.click().then(function() {
        that.headerDeleteDowntimesCheckbox.click().then(function() {
            that.deleteDowntimesButton.click().then(function() {
                var ready = false;
                P.wait(function() {
                    that.downtimesTabHeader.getText().then(function(text) {
                        if (text === 'Downtimes (0)') {
                            ready = true;
                        }
                    });
                    return ready;
                }, 20000);
                cb();
            });
        });
    });
};

module.exports = Downtimes;
