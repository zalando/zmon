var P = protractor.getInstance();
var Dashboard = function() {};

Dashboard.prototype.searchForm = element(by.model('dashboardFilter'));

Dashboard.prototype.newDashboardButton = element(by.css('a.btn.btn-primary'));

Dashboard.prototype.dashboardButton = element(by.css('.nav.navbar-nav li a[href="#dashboards"]'));

Dashboard.prototype.checkDefButton = element(by.css('.nav.navbar-nav li a[href="#check-definitions"]'));

Dashboard.prototype.alertDefButton = element(by.css('.nav.navbar-nav li a[href="#alert-definitions"]'));

Dashboard.prototype.reportButton = element(by.css('.nav.navbar-nav li a[href="#reports"]'));

Dashboard.prototype.trialRunButton = element(by.css('.nav.navbar-nav li a[href="#trial-run"]'));

module.exports = Dashboard;
