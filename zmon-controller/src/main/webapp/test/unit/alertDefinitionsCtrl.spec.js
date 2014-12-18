describe('AlertDefinitionsCtrl', function() {
    var scope, controller, httpBackend;

    beforeEach(function() {
        // Fake the module's UserInfoService dependency
        angular.mock.module('zmon2App', function($provide) {
            $provide.factory('UserInfoService', function() {
                return {
                    get: function() {
                        return {
                            'fakeKey': 'fakeValue'
                        };
                    }
                };
            });
        });

        angular.mock.inject(function($rootScope, $controller, $httpBackend) {
            scope = $rootScope.$new();

            controller = $controller('AlertDefinitionCtrl', {
                $scope: scope
            });

            httpBackend = $httpBackend;

            httpBackend.when('GET', 'rest/allAlerts?').respond(["Backend/Order", "Backend/Payment", "Platform/System"]);
            httpBackend.when('GET', 'rest/alertDefinitions?').respond([{
                "id": 691,
                "name": "Alert on http code (1) --",
                "description": "Alert description",
                "team": "Backend/Order",
                "responsible_team": "Platform/Software",
                "entities": [{
                    "project": "shop",
                    "environment": "release-staging",
                    "type": "zomcat"
                }],
                "condition": "!=0",
                "notifications": ["send_mail('vitalii.kapara@zalando.de')"],
                "check_definition_id": 2,
                "status": "ACTIVE",
                "priority": 1,
                "last_modified": 1396619805429,
                "last_modified_by": "hjacobs",
                "period": "xxxxx",
                "editable": true,
                "cloneable": true,
                "deletable": true
            }, {
                "id": 695,
                "name": "Alert on http code1",
                "description": "Alert description",
                "team": "Platform",
                "responsible_team": "Platform/System",
                "entities": [],
                "condition": "!=0",
                "notifications": [],
                "check_definition_id": 2,
                "status": "INACTIVE",
                "priority": 1,
                "last_modified": 1396362646573,
                "last_modified_by": "hjacobs",
                "period": null,
                "editable": true,
                "cloneable": true,
                "deletable": true
            }]);

        });
    });

    afterEach(function() {
        httpBackend.verifyNoOutstandingExpectation();
        httpBackend.verifyNoOutstandingRequest();
    });


    it('should initially have three alert teams, two alert definitions and two alert statuses', function() {
        httpBackend.expectGET('rest/allAlerts?');
        httpBackend.expectGET('rest/alertDefinitions?');
        httpBackend.flush();
        expect(scope.alertTeams.length).toBe(3);
        expect(scope.allAlertDefinitions.length).toBe(2);
        expect(scope.alertStatuses.length).toBe(2);
    });

    it('should have one alert after applying filter for "ACTIVE" alerts only', function() {
        httpBackend.flush();
        scope.setAlertsFilter('ACTIVE');
        expect(scope.alertDefinitionsByStatus.length).toBe(1);
    });

});
