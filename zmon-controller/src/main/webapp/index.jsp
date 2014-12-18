<%@ taglib prefix="security" uri="http://www.springframework.org/security/tags" %>
<%@ taglib prefix="c" uri="http://java.sun.com/jsp/jstl/core" %>

<!DOCTYPE html>
<html ng-app="zmon2App" ng-controller="IndexCtrl">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta property="sessionExpiredUrl" content="logout?error=session_expired" />
    <title>ZMON 2.0</title>

    <link rel="stylesheet" type="text/css" href="asset/css/zalando-bootstrap.css?t=${buildTime}" />
    <link rel="stylesheet" type="text/css" href="styles/main.css?t=${buildTime}" />
    <link rel="stylesheet" type="text/css" href="styles/charts.css?t=${buildTime}" />
    <link rel="stylesheet" type="text/css" href="styles/dashboard.css?t=${buildTime}" />
    <link rel="stylesheet" type="text/css" href="styles/errors.css?t=${buildTime}" />
    <link rel="stylesheet" type="text/css" href="styles/forms.css?t=${buildTime}" />
    <link rel="stylesheet" type="text/css" href="styles/select2/zmon-select2.css?t=${buildTime}" />
    <link rel="stylesheet" type="text/css" href="styles/select2/select2-bootstrap.css?t=${buildTime}" />
    <link rel="stylesheet" type="text/css" href="styles/select2/select2.css?t=${buildTime}" />

    <script src="lib/stacktrace/stacktrace.js?time=${buildTime}"></script>
    <script src="lib/jquery/jquery.min.js?time=${buildTime}"></script>
    <script src="lib/bootstrap/bootstrap.min.js?time=${buildTime}"></script>
    <script src="lib/angularjs/angular.min.js?time=${buildTime}"></script>
    <script src="lib/angular-local-storage/angular-local-storage.min.js?time=${buildTime}"></script>
    <script src="lib/angularjs/angular-cookies.min.js?time=${buildTime}"></script>
    <script src="lib/angularjs/angular-sanitize.min.js?time=${buildTime}"></script>
    <script src="lib/angularjs/angular-route.min.js?time=${buildTime}"></script>
    <script src="lib/ui-bootstrap/ui-bootstrap.min.js?time=${buildTime}"></script>

    <script src="lib/flot/jquery.flot.min.js?time=${buildTime}"></script>
    <script src="lib/flot/jquery.flot.time.min.js?time=${buildTime}"></script>
    <script src="lib/flot/jquery.flot.selection.min.js?time=${buildTime}"></script>
    <script src="lib/flot/jquery.flot.stack.min.js?time=${buildTime}"></script>
    <script src="lib/flot/jquery.flot.tooltip.min.js?time=${buildTime}"></script>
    <script src="lib/lodash/lodash.min.js?time=${buildTime}"></script>
    <script src="lib/moment/moment.min.js?time=${buildTime}"></script>

    <script src="lib/raphael/raphael.2.1.0.min.js?time=${buildTime}"></script>
    <script src="lib/justgage/justgage.1.0.1.js?time=${buildTime}"></script>
    <script src="lib/showdown/showdown.js?time=${buildTime}"></script>
    <script src="lib/ace/ace.js?time=${buildTime}" charset="utf-8"></script>
    <script src="lib/jsonpath/jsonpath.js?time=${buildTime}" charset="utf-8"></script>
    <script src="lib/js-yaml/js-yaml.min.js?time=${buildTime}"></script>
    <script src="lib/piwik/piwik.min.js?time=${buildTime}" charset="utf-8"></script>
    <script src="lib/angulartics/angulartics.min.js?time=${buildTime}" charset="utf-8"></script>
    <script src="lib/angulartics/angulartics-piwik.min.js?time=${buildTime}" charset="utf-8"></script>
    <script src="lib/select2/select2.min.js?time=${buildTime}" charset="utf-8"></script>
    <script src="lib/colorhash/colorhash.js?time=${buildTime}" charset="utf-8"></script>
</head>
<body ng-class="activePage">
    <div class="loading-indicator" ng-show="IndexCtrl.getLoadingIndicatorState()">
        Loading...
    </div>
    <nav class="navbar navbar-inverse" role="navigation">
        <div class="span12">
            <div class="navbar-header">
                <a class="navbar-brand" href="#"><img src="/logo.png"> ZMON 2.0</a>
                <button type="button" class="navbar-toggle" data-toggle="collapse" data-target=".navbar-collapse">
                  <span class="sr-only">Toggle navigation</span>
                  <span class="icon-bar"></span>
                  <span class="icon-bar"></span>
                  <span class="icon-bar"></span>
                </button>
                <div class="collapse navbar-collapse navbar-left">
                    <ul class="nav navbar-nav">
                        <li ng-class="{'active-page': activePage == 'dashboards'}"><a href="#dashboards">Dashboards</a></li>
                        <security:authorize access="isAuthenticated()">
                            <li ng-class="{'active-page': activePage == 'check-definitions'}"><a href="#check-definitions" >Check defs</a></li>
                            <li ng-class="{'active-page': activePage == 'alert-definitions'}"><a href="#alert-definitions" >Alert defs</a></li>
                            <li ng-class="{'active-page': activePage == 'reports'}" ng-show="IndexCtrl.userInfo['history-report-access']"><a href="#reports" >Reports</a></li>
                        </security:authorize>
                        <c:if test="${hasTrialRunPermission}">
                            <li ng-class="{'active-page': activePage == 'trial-run'}"><a href="#trial-run" >Trial Run</a></li>
                        </c:if>
                    </ul>
                </div>
                <div class="navbar-text navbar-right" ng-cloak>
                    <span ng-class="{invisible: !serviceStatus.hasDataRefresh}">
                        <start-stop refreshing="serviceStatus.isDataRefreshing" start-refresh-callback="resumeDataRefresh()" stop-refresh-callback="pauseDataRefresh()" ></start-stop>
                    </span>
                    <span class="app-status" ng-show="serviceStatus.isStatusRefreshing" tooltip-html-unsafe="{{statusTooltip}}" tooltip-placement="bottom">
                        <strong ng-class="serviceStatus.queueSize > 1000 ? 'warning' : 'ok'">{{serviceStatus.queueSize}}</strong> in queue,
                        <strong ng-class="serviceStatus.workersActive < serviceStatus.workersTotal ? 'warning' : 'ok'">{{ serviceStatus.workersActive}}/{{ serviceStatus.workersTotal}}</strong> active workers,
                        <strong>{{ checksPerSecond | number:2 }}</strong>/s
                        <strong class="app-last-update" ng-class="{warning:alertsOutdated}" ng-show="activePage === 'dashboard'">{{alertsLastUpdate | time}}</strong>
                    </span>
                    <span ng-show="!serviceStatus.isStatusRefreshing">
                        Initializing status...
                    </span>
                    <span class="app-status">
                        <a title="ZMON Documentation" target="docs" href="http://zmon.readthedocs.org/">
                            <i class="fa fa-question-circle fa-lg"></i>
                        </a>
                    </span>
                    <security:authorize access="isAnonymous()">
                        <span class="auth">
                            <a class="auth-action" ng-href="/login.jsp">Log in</a>
                        </span>
                    </security:authorize>
                    <security:authorize access="isAuthenticated()">
                        <span class="auth"
                            data-user="${userName}"
                            data-teams="${teams}"
                            data-schedule-downtime="${hasScheduleDowntimePermission}"
                            data-delete-downtime="${hasDeleteDowntimePermission}"
                            data-add-comment="${hasAddCommentPermission}"
                            data-add-alert-def="${hasAddAlertDefinitionPermission}"
                            data-add-dashboard="${hasAddDashboardPermission}"
                            data-history-report-access="${hasHistoryReportAccess}"
                            data-instantaneous-alert-evaluation="${hasInstantaneousAlertEvaluationPermission}">

                            <button type="button" class="auth-user btn btn-default dropdown-toggle" data-toggle="dropdown">
                                ${userName}
                                <span class="caret"></span>
                            </button>
                            <ul class="dropdown-menu" role="menu">
                                <li><a href="logout">Logout</a></li>
                            </ul>
                       </span>
                    </security:authorize>
                </div>
            </div>
        </div>
    </nav>

    <div id="main" ng-view></div>

    <div id="message-manager-wrapper">
        <span class="message"></span>
    </div>
</body>

<script src="js/app.js?time=${buildTime}"></script>
<script src="js/filters/entities.js?time=${buildTime}"></script>
<script src="js/filters/timespan.js?time=${buildTime}"></script>
<script src="js/filters/datetime.js?time=${buildTime}"></script>
<script src="js/filters/time.js?time=${buildTime}"></script>
<script src="js/filters/prettify.js?time=${buildTime}"></script>
<script src="js/filters/markdown.js?time=${buildTime}"></script>
<script src="js/filters/epochToDate.js?time=${buildTime}"></script>
<script src="js/filters/downtimeReasons.js?time=${buildTime}"></script>
<script src="js/filters/inDisplayedGroup.js?time=${buildTime}"></script>
<script src="js/filters/encodeUri.js?time=${buildTime}"></script>
<script src="js/directives/priority.js?time=${buildTime}"></script>
<script src="js/directives/status.js?time=${buildTime}"></script>
<script src="js/directives/chart.js?time=${buildTime}"></script>
<script src="js/directives/gauge.js?time=${buildTime}"></script>
<script src="js/directives/trend.js?time=${buildTime}"></script>
<script src="js/directives/startStop.js?time=${buildTime}"></script>
<script src="js/directives/dashboardWidget.js?time=${buildTime}"></script>
<script src="js/directives/networkMap.js?time=${buildTime}"></script>
<script src="js/directives/json.js?time=${buildTime}"></script>
<script src="js/directives/expand.js?time=${buildTime}"></script>
<script src="js/directives/focus.js?time=${buildTime}"></script>
<script src="js/directives/infiniteScroll.js?time=${buildTime}"></script>
<script src="js/directives/commentDialog.js?time=${buildTime}"></script>
<script src="js/directives/entityFilterContainer.js?time=${buildTime}"></script>
<script src="js/directives/entityFilterForm.js?time=${buildTime}"></script>
<script src="js/directives/widgetConfigContainer.js?time=${buildTime}"></script>
<script src="js/directives/widgetConfigChart.js?time=${buildTime}"></script>
<script src="js/directives/codeEditor.js?time=${buildTime}"></script>
<script src="js/directives/repeatMonitor.js?time=${buildTime}"></script>
<script src="js/directives/modelChangeBlur.js?time=${buildTime}"></script>
<script src="js/directives/select2.js?time=${buildTime}"></script>
<script src="js/directives/clickOutside.js?time=${buildTime}"></script>
<script src="js/services/MainAlertService.js?time=${buildTime}"></script>
<script src="js/services/CommunicationService.js?time=${buildTime}"></script>
<script src="js/services/FeedbackMessageService.js?time=${buildTime}"></script>
<script src="js/services/HttpResponseInterceptor.js?time=${buildTime}"></script>
<script src="js/services/UserInfoService.js?time=${buildTime}"></script>
<script src="js/services/DowntimesService.js?time=${buildTime}"></script>
<script src="js/services/PreconditionsService.js?time=${buildTime}"></script>
<script src="js/services/LoadingIndicatorService.js?time=${buildTime}"></script>
<script src="js/controllers/DashboardCtrl.js?time=${buildTime}"></script>
<script src="js/controllers/AlertDetailsCtrl.js?time=${buildTime}"></script>
<script src="js/controllers/AlertDefinitionCtrl.js?time=${buildTime}"></script>
<script src="js/controllers/CheckDefinitionCtrl.js?time=${buildTime}"></script>
<script src="js/controllers/DashboardDefinitionCtrl.js?time=${buildTime}"></script>
<script src="js/controllers/AlertDefinitionEditCtrl.js?time=${buildTime}"></script>
<script src="js/controllers/DashboardConfigurationCtrl.js?time=${buildTime}"></script>
<script src="js/controllers/CheckChartsCtrl.js?time=${buildTime}"></script>
<script src="js/controllers/ReportsCtrl.js?time=${buildTime}"></script>
<script src="js/controllers/TrialRunCtrl.js?time=${buildTime}"></script>
<script src="js/controllers/HistoryCtrl.js?time=${buildTime}"></script>

<script type="text/javascript">
    angular.module('zmon2App').controller('IndexCtrl', ['$scope', '$location', 'localStorageService', 'MainAlertService', '$interval', 'APP_CONST', 'LoadingIndicatorService', 'UserInfoService',
        function($scope, $location, localStorageService, MainAlertService, $interval, APP_CONST, LoadingIndicatorService, UserInfoService) {
            $scope.IndexCtrl = this;
            $scope.IndexCtrl.activePage = null; // will be set be corresponding controller i.e. from the child $scope
            $scope.statusTooltip = "Loading status...";
            $scope.checksPerSecond = 0;
            $scope.serviceStatus = {};
            $scope.checkInvocationsCache = {};

            this.userInfo = UserInfoService.get();

            // Helper, decides if support icon should be shown based
            // on the user team (Incident team only for now).
            this.showSupportIcon = function() {
                var userTeams = " ";

                if ($scope.IndexCtrl.userInfo.teams) {
                    userTeams = $scope.IndexCtrl.userInfo.teams;
                }

                if (_.isArray(userTeams)) {
                    userTeams = userTeams.join();
                }

                return userTeams.toLowerCase().indexOf("incident") >= 0;
            };

            this.getLoadingIndicatorState = function() {
                return LoadingIndicatorService.getState();
            };

            $scope.pauseDataRefresh = function() {
                MainAlertService.pauseDataRefresh();
            };
            $scope.resumeDataRefresh = function() {
                MainAlertService.resumeDataRefresh();
            };

            $scope.$on('$routeChangeStart', function() {
                localStorageService.set('returnTo', '/#' + $location.path());
            });

            // Start periodic refresh of the app's overall status only (Q-size etc.)
            // Not related to the periodic data refresh that the page content might by having (e.g. dashboard, alert details etc.)
            // The periodoc data refresh of the pages that have it are defined in MainAlertService.status's 'hasDataRefresh' and 'isDataRefreshing'
            $scope.alertsOutdated = false;

            // Refresh status helper.
            var refreshStatus = function () {
                var currentStatus = MainAlertService.getStatus();
                var statusHtml = "<div class='app-status-tooltip'>";

                $scope.statusTooltip = "";
                $scope.alertsOutdated = new Date()/1000 - $scope.alertsLastUpdate > 30 ? true : false;

                // Sort queues and workers.
                currentStatus.workers = _.sortBy(currentStatus.workers, "name");
                currentStatus.queues = _.sortBy(currentStatus.queues, "name");

                // Get workers detailed status.
                statusHtml += "<div class='workers'><h6>Workers</h6>";
                var schedulerHtml = "";

                _.each(currentStatus.workers, function(worker) {
                    if(worker.name.indexOf('s-')!=0) {
                        statusHtml += "<div>";
                        statusHtml += "<span class='name'>" + worker.name + "</span>";
                        statusHtml += "<span class='calls'>" + worker.checksPerSecond.toFixed(2) + "/s</span>";
                        statusHtml += "<span class='last'> " + worker.lastExecutionTime + "</span>";
                        statusHtml += "</div>";
                    }
                    else {
                        schedulerHtml += "<div>";
                        schedulerHtml += "<span class='name'>" + worker.name.substr(2) + "</span>";
                        schedulerHtml += "<span class='calls'>" + worker.checksPerSecond.toFixed(2) + "/s</span>";
                        schedulerHtml += "<span class='last'> " + worker.lastExecutionTime + "</span>";
                        schedulerHtml += "</div>";
                    }
                });

                statusHtml += "</div>";

                // Get workers detailed status.
                statusHtml += "<div class='workers'><h6>Schedulers</h6>";
                statusHtml += schedulerHtml;
                statusHtml += "</div>";

                // Get queues detailed status.
                statusHtml += "<div class='queues'><h6>Queues</h6>";
                _.each(currentStatus.queues, function(queue) {
                    statusHtml += "<div>";
                    statusHtml += "<span class='name'>" + queue.name + "</span>";
                    statusHtml += "<span class='size'>size " + queue.size + "</span>";
                    statusHtml += "</div>";
                });
                statusHtml += "</div>";

                statusHtml += "</div>";

                $scope.statusTooltip = statusHtml;
                $scope.serviceStatus = currentStatus;
                $scope.checksPerSecond = currentStatus.checksPerSecond;
            };

            // Start refreshing workers / queue status.
            $interval(refreshStatus, 2000);
            refreshStatus();

            String.prototype.format = function() {
                var args = arguments;
                var i = 0;
                return this.replace(/\{(\w*)?:?(\.\d*f)?\}/g, function(match, key, format) {
                    var value = '';
                    key = (typeof key === 'undefined' || key === '') ? 0 : key;
                    value = typeof args[i] === 'object' ? args[i][key] : args[key];

                    if (format) {
                        var fp = format.match(/\.(\d*)f/)[1];
                        value = parseFloat(value).toFixed(fp);
                    }

                    i++;
                    return value;
                });
            };

        }]);
</script>
</html>
