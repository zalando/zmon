describe('CheckDefinitionsCtrl', function() {
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

            controller = $controller('CheckDefinitionCtrl', {
                $scope: scope
            });

            httpBackend = $httpBackend;

            httpBackend.when('GET', 'rest/checkDefinitions?').respond([{
                "id": 34,
                "name": "Heartbeat Check 7871",
                "description": "### Test alert on all keys.\n\n* a\n* b\n  * b.1",
                "technical_details": "",
                "potential_analysis": "",
                "potential_impact": "",
                "potential_solution": "",
                "owning_team": "Backend/Logistics",
                "entities": [{
                    "type": "zomcat"
                }],
                "interval": 2,
                "command": "http(\"/heartbeat.jsp\")",
                "status": "INACTIVE",
                "source_url": "https://scm.example.org/projects/PLATFORM/repos/systemapp",
                "last_modified_by": "pribeiro"
            }]);

        });
    });

    afterEach(function() {
        httpBackend.verifyNoOutstandingExpectation();
        httpBackend.verifyNoOutstandingRequest();
    });


    it('should initially have one check definition entry', function() {
        httpBackend.expectGET('rest/checkDefinitions?');
        httpBackend.flush();
        expect(scope.checkDefinitions.length).toBe(1);
    });

});