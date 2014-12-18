describe('TrialRunCtrl', function() {
    var scope, controller;
    var expectedYAML = 'status: INACTIVE\n\
name: ""\n\
description: ""\n\
command: |\n\
null\n\
entities:\n\
# MANDATORY FIELD:\n\
#interval:\n\
# OPTIONAL FIELDS\n\
#technical_details: Optional Technical Details\n\
#potential_analysis: Optional Potential analysis\n\
#potential_impact: Optional potential impact\n\
#potential_solution: Optional potential solution';

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

        angular.mock.inject(function($rootScope, $controller) {
            scope = $rootScope.$new();
            scope.alert = {};
            scope.alert.name = 'test-yaml';
            scope.alert.check_command = 'sql().execute("""select 1 as a, now() as b""").results()';
            scope.alert.entities = '[{"type": "database","environment": "live","name":"customer", "role":"master"}]';

            controller = $controller('TrialRunCtrl', {
                $scope: scope
            });
        });
    });

    it('should build valid YAML', function() {
        expect(scope.TrialRunCtrl.buildYAMLContent()).toEqual(expectedYAML);
    });
});