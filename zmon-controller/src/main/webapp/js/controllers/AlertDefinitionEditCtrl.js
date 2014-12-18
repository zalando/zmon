angular.module('zmon2App').controller('AlertDefinitionEditCtrl', ['$scope', '$routeParams', '$location', 'MainAlertService', 'CommunicationService', 'FeedbackMessageService', 'UserInfoService', 'APP_CONST',
    function($scope, $routeParams, $location, MainAlertService, CommunicationService, FeedbackMessageService, UserInfoService, APP_CONST) {

        // Set in parent scope which page is active for the menu styling
        $scope.$parent.activePage = 'alert-definitions'; // is not a menu option, but still set
        $scope.invalidFormat = false;
        $scope.showDescriptionPreview = false;
        $scope.entityFilter = {};
        $scope.entityExcludeFilter = {};
        $scope.alertParameters = [];
        $scope.paramTypes = ['string', 'int', 'boolean', 'date'];
        $scope.allTags = [];
        $scope.defaultEntitiesFilter = undefined;
        $scope.defaultEntitiesExcludeFilter = undefined;
        $scope.defaultNotifications = undefined;
        var userInfo = UserInfoService.get();

        // Entity filter types initialized by default with GLOBAL (which is not provided by backend as separate type) and the rest comes from backend
        $scope.entityFilter.types = [{
            "type": "GLOBAL"
        }];
        $scope.entityExcludeFilter.types = [{
            "type": "GLOBAL"
        }];

        // User can define the entity filters either as plain JSON text or through a form which corresponds to an array of objects
        $scope.entityFilter.formEntityFilters = [];
        $scope.entityFilter.textEntityFilters = '[]';
        $scope.entityExcludeFilter.formEntityFilters = [];
        $scope.entityExcludeFilter.textEntityFilters = '[]';

        // Flag to toggle UI on whether user types JSON text or uses form to define the entity filters
        $scope.entityFilterInputMethod = 'text';
        $scope.entityExcludeFilterInputMethod = 'text';

        // Keep account of overwritten Properties and Parameters on inherit mode
        $scope.oProps = [];
        $scope.oParams = [];

        // List of properties that shouldn't be inherited from a parent alert
        $scope.nonInheritableProperties = [ 'id', 'check_definition_id', 'editable', 'cloneable', 'deleteable',
            'template', 'last_modified', 'last_modified_by', 'parent_id', 'parameters' ]

        $scope.priorityOptions = [
            {
                'value': 1,
                'label': 'Priority 1 (red)'
            },
            {
                'value': 2,
                'label': 'Priority 2 (orange)'
            },
            {
                'value': 3,
                'label': 'Priority 3 (yellow)'
            }
        ];

        $scope.statusOptions = [
            {
                'value': 'ACTIVE',
                'label': 'ACTIVE'
            },
            {
                'value': 'INACTIVE',
                'label': 'INACTIVE'
            },
            {
                'value': 'REJECTED',
                'label': 'REJECTED'
            }
        ];

        $scope.parameterTypeOptions = [
            {
                'value': 'str',
                'label': 'String'
            },
            {   'value': 'int',
                'label': 'Integer'
            },
            {   'value': 'float',
                'label': 'Float'
            },
            {
                'value': 'bool',
                'label': 'Boolean'
            },
            {
                'value': 'date',
                'label': 'Date'
            }
        ];

        $scope.parameterTypeBooleanOptions = [
            {
                'value': true,
                'label': 'True'
            },
            {
                'value': false,
                'label': 'False'
            }
        ];

        $scope.INDENT = '    ';

        // for route '/alert-definitions/add/:checkDefinitionId' [add alert]
        $scope.alertDefinitionId = $routeParams.alertDefinitionId;
        // for route '/alert-definitions/edit/:alertDefinitionId' [edit existing alert]
        $scope.checkDefinitionId = $routeParams.checkDefinitionId;
        // for route '/alert-definitions/clone/:cloneFromAlertDefinitionId' [clone from existing alert]
        $scope.cloneFromAlertDefinitionId = $routeParams.cloneFromAlertDefinitionId;
        // for route '/alert-definitions/inherit/:parentAlertDefinitionId' [inherit from existing alert]
        $scope.parentAlertDefinitionId = $routeParams.parentAlertDefinitionId;

        // Partial version of alert, only contains overwritten fields (a.k.a. alert diff)
        $scope.alertDefinitionNode = {};

        // Parent alert definition, merged alert from higher alerts in tree (no diff).
        $scope.parentAlertDefinition = {};

        // Final merged version of alert definition: parentAlertDefiniton + alertDefinitionNode
        $scope.alertDefinition = null;

        $scope.focusedElement = null;

        $scope.save = function() {
            if ($scope.adForm.$valid) {
                try {
                    if ($scope.alertDefinition.template && $scope.entityFilter.textEntityFilters === '') {
                        delete $scope.alertDefinition.entities;
                    } else {
                        $scope.alertDefinition.entities = JSON.parse($scope.entityFilter.textEntityFilters);
                    }
                    if ($scope.alertDefinition.template && $scope.entityExcludeFilter.textEntityFilters === '') {
                        delete $scope.alertDefinition.entities_exclude;
                    } else {
                        $scope.alertDefinition.entities_exclude = JSON.parse($scope.entityExcludeFilter.textEntityFilters);
                    }
                    if ($scope.alertDefinition.template && ($scope.notificationsJson == undefined || $scope.notificationsJson == '')) {
                        delete $scope.alertDefinition.notifications;
                    } else {
                        $scope.alertDefinition.notifications = JSON.parse($scope.notificationsJson);
                    }
                    if ($scope.oParams.length === 0) {
                        delete $scope.alertDefinition.parameters;
                    } else {
                        $scope.alertDefinition.parameters = $scope.formParametersObject();
                    }
                    var alert = $scope.alertDefinition;

                    // Set period to empty string, in case it wasn't defined and its not being inherited.
                    if (typeof alert.period === 'undefined') {
                        alert.period = "";
                    }
                    // In case of an inherited alert, only send diff
                    if ($scope.alertDefinition.parent_id || $scope.mode === 'inherit') {
                        alert = $scope.getInheritanceDiff();
                    }

                    CommunicationService.updateAlertDefinition(alert).then(function(data) {
                        FeedbackMessageService.showSuccessMessage('Saved successfully; redirecting...', 500, function() {
                            $location.path('/alert-details/' + data.id);
                        });
                    });
                } catch (ex) {
                    $scope.invalidFormat = true;
                    return FeedbackMessageService.showErrorMessage('JSON format is incorrect' + ex);
                }
            } else {
                $scope.adForm.submitted = true;
                $scope.focusedElement = null;
            }
        };

        $scope.cancel = function() {
            $scope.adForm.submitted = false;
            if ($scope.mode === 'edit') {
                $location.path('/alert-details/' + $scope.alertDefinitionId);
            } else if ($scope.mode === 'clone') {
                $location.path('/alert-details/' + $scope.cloneFromAlertDefinitionId);
            } else {
                $location.path('/check-definitions/view/' + $scope.checkDefinitionId);
            }
        };

        // Generate a json object with only overwritten properties.
        $scope.getInheritanceDiff = function() {
            var result = {};
            _.each($scope.oProps, function(property) {
                result[property] = $scope.alertDefinition[property];
            });
            if ($scope.mode === 'edit') {
                result.id = $scope.alertDefinition.id;
            }
            if ($scope.oParams.length) {
                result.parameters = $scope.formParametersObject();
            }
            result.parent_id = $scope.getInheritParentId();
            result.template = $scope.alertDefinition.template;
            result.team = $scope.alertDefinition.team;
            result.responsible_team = $scope.alertDefinition.responsible_team;
            result.status = $scope.alertDefinition.status;
            result.check_definition_id = $scope.alertDefinition.check_definition_id;
            return result;
        };

        // Get appropriate ID of parent alert.
        $scope.getInheritParentId = function() {
            if ($scope.mode === 'inherit') {
                return $scope.alertDefinition.id;
            }
            return $scope.alertDefinition.parent_id || null;
        };

        // Get a check definition from the backend
        $scope.getCheckDefinition = function() {
            CommunicationService.getCheckDefinition($scope.checkDefinitionId).then(
                function(response) {
                    $scope.checkDefinition = response;
                    if ($scope.alertDefinition === null) {
                        $scope.alertDefinition = {
                            check_definition_id: $scope.checkDefinition.id,
                            team: $scope.defaultTeam || "",
                            responsible_team: $scope.defaultRespTeam || "",
                            entities: [],
                            entities_exclude: [],
                            notifications: [],
                            template: false
                        };
                    }
                }
            );
        };

        // Get an alert definition and its parent (when available) from the backend.
        $scope.getAlertDefinition = function(alertId, cb) {
            CommunicationService.getAlertDefinitionNode(alertId).then(function(data) {
                $scope.alertDefinitionNode = data;
                $scope.alertDefinition = extendAlert(data);
                $scope.checkDefinitionId = data.check_definition_id;
                $scope.getCheckDefinition();

                $scope.alertParameters = [];
                _.each(_.keys(data.parameters).sort(), function(name) {
                    $scope.oParams.push(name);
                    if (data.parameters[name].type === 'date') {
                        data.parameters[name].value = new Date(data.parameters[name].value);
                    }
                    $scope.alertParameters.push(_.extend({'name': name}, data.parameters[name]));
                });

                // When the alert has a parent, get data from parent and merge into empty fields.
                if ($scope.alertDefinition.parent_id) {
                    // Set overwritten fields when alert is inherited, but only for edit and clone modes.
                    if ($scope.mode !== 'inherit') {
                        markAllAsOverwritten();
                    }
                    $scope.getParentAlertDefinition($scope.alertDefinition.parent_id, function() {
                        $scope.mergeNode();
                        $scope.resetEntityFilter();
                        $scope.resetEntityExcludeFilter();
                        $scope.resetNotifications();
                        if (cb) { return cb(); }
                    });
                } else {
                    $scope.parentAlertDefinition = extendAlert(data);
                    if (cb) { return cb(); }
                }
            });
        };

        // Get an alert from a parent Id
        $scope.getParentAlertDefinition = function(alertId, cb) {
            CommunicationService.getAlertDefinition(alertId).then(function(data) {
                $scope.parentAlertDefinition = data;
                return cb();
            });
        }

        // Merge Node (diff) with parent data to have a complete alert definition.
        $scope.mergeNode = function() {
            _.each($scope.alertDefinition, function(value, property) {
                if (value === null && property !== 'parameters') {
                    $scope.oProps = _.without($scope.oProps, property);
                    $scope.alertDefinition[property] = angular.copy($scope.parentAlertDefinition[property]);
                }
            });
            if ($scope.alertDefinition.parameters == null && $scope.parentAlertDefinition.parameters) {
                $scope.alertDefinition.parameters = [];
            }
            _.each($scope.alertDefinition.parent_id && $scope.parentAlertDefinition.parameters, function(p, name) {
                if ($scope.oParams.indexOf(name) === -1) {
                    $scope.alertParameters.push(_.extend({"name": name}, p));
                    $scope.alertDefinition.parameters[name] = p;
                }
            });
        };

        // Manage key-up events
        $scope.markAsOverwritten = function(property) {
            if ($scope.oProps.indexOf(property) === -1) {
                $scope.oProps.push(property)
            };
        };

        $scope.markAsOverwrittenParam = function(name) {
            if ($scope.oParams.indexOf(name) === -1) {
                $scope.oParams.push(name)
            }
        };

        // Add all overwritten properties from current alert to array
        var markAllAsOverwritten = function() {
            _.each($scope.alertDefinition, function(value, property) {
                if (value !== null && $scope.nonInheritableProperties.indexOf(property) === -1) {
                    $scope.markAsOverwritten(property);
                }
            });
        };

        // Reset entity filter to inherit values again
        $scope.resetEntityFilter = function() {
            var entities = $scope.alertDefinition.entities || $scope.parentAlertDefinition.entities || $scope.defaultEntitiesFilter;
            var str = JSON.stringify(entities, null, $scope.INDENT);
            $scope.entityFilter.textEntityFilters = str;
            $scope.entityFilter.formEntityFilters = entities;
        };

        // Reset entity EXCLUDE filter to inherit values again
        $scope.resetEntityExcludeFilter = function() {
            var entitiesExclude = $scope.alertDefinition.entities_exclude || $scope.parentAlertDefinition.entities_exclude || $scope.defaultEntitiesExcludeFilter;
            var str = JSON.stringify(entitiesExclude, null, $scope.INDENT);
            $scope.entityExcludeFilter.textEntityFilters = str;
            $scope.entityExcludeFilter.formEntityFilters = entitiesExclude;
        };

        // Reset Notifications array from Alert Definition
        $scope.resetNotifications = function() {
            var notifications = $scope.alertDefinitionNode.notifications || $scope.parentAlertDefinition.notifications || $scope.defaultNotifications;
            $scope.notificationsJson = JSON.stringify(notifications, null, $scope.INDENT);
        };

        // Add a new parameter with cleared values and type string by default
        $scope.addParameter = function() {
            $scope.alertParameters.push({type: 'str'});
        };

        // Remove a parameter from the parameters json object
        $scope.removeParameter = function(name) {
            var index = null;
            _.each($scope.alertParameters, function(param, i) {
                if (param.name === name) {
                    index = i;
                };
            });
            if (index != null) {
                $scope.alertParameters.splice(index, 1);
            }
        };

        // Get current parameters in form and generate a properly formatted
        // json to send to the backend.
        $scope.formParametersObject = function() {
            var parameters = {};
            _.each($scope.oParams, function(p) {
                _.each($scope.alertParameters, function(param) {
                    if (param.name === p) {
                        var val = param.value;

                        if (param.type === 'int') {
                            val = parseInt(param.value);
                        }
                        if (param.type === 'float') {
                            val = parseFloat(param.value);
                        }
                        if (param.type === 'date') {
                            var d = new Date(val);
                            // FIXME Date should be seconds since epoch. Current format is temporary because python implementation needs to be changed to seconds also.
                            val = d.getFullYear() + '-' + (d.getMonth() + 1) + '-' + d.getDate() + 'T00:00:00.000Z';
                        }

                        parameters[param.name] = {
                            "value": val,
                            "comment": param.comment,
                            "type": param.type
                        }
                    }
                });
            });
            return parameters;
        };

        // Add a tag to the tags array
        $scope.addTag = function(tag) {
            if (typeof $scope.alertDefinition.tags === 'undefined' || $scope.alertDefinition.tags == null) {
                $scope.alertDefinition.tags = [];
            }
            if ($scope.alertDefinition.tags.indexOf(tag.text) === -1) {
                $scope.alertDefinition.tags.push(tag.text);
                $scope.markAsOverwritten('tags');
            };
        };

        // Remove a tag from the tags array
        $scope.removeTag = function(tag) {
            $scope.alertDefinition.tags = _.without($scope.alertDefinition.tags, tag.id);
            $scope.markAsOverwritten('tags');
        };

        // Revert only one property back to its inherited parent value
        $scope.inheritProperty = function(property) {
            $scope.oProps = _.without($scope.oProps, property);

            if (property === 'entities') {
                $scope.alertDefinition.entities = angular.copy($scope.parentAlertDefinition.entities);
                $scope.entityFilter.formEntityFilters = $scope.alertDefinition.entities;
                if ($scope.alertDefinition.entities) {
                    return $scope.entityFilter.textEntityFilters = JSON.stringify($scope.alertDefinition.entities, null, $scope.INDENT);
                }
                return $scope.entityFilter.textEntityFilters = undefined;
            }

            if (property === 'entities_exclude') {
                $scope.alertDefinition.entities_exclude = angular.copy($scope.parentAlertDefinition.entities_exclude);
                $scope.entityExcludeFilter.formEntityFilters = $scope.alertDefinition.entities_exclude;
                if ($scope.alertDefinition.entities_exclude) {
                    return $scope.entityExcludeFilter.textEntityFilters = JSON.stringify($scope.alertDefinition.entities_exclude, null, $scope.INDENT);
                }
                return $scope.entityExcludeFilter.textEntityFilters = undefined;
            }

            if (property === 'notifications') {
                if ($scope.parentAlertDefinition.notifications) {
                    $scope.alertDefinition.notifications = angular.copy($scope.parentAlertDefinition.notifications);
                    return $scope.notificationsJson = JSON.stringify($scope.alertDefinition.notifications, null, $scope.INDENT);
                }
                return $scope.notificationsJson = undefined;
            }

            $scope.alertDefinition[property] = $scope.parentAlertDefinition[property];
        };

        // Revert only one parameter back to its inherited parent value
        $scope.inheritParameter = function(param) {
            $scope.oParams = _.without($scope.oParams, param);
            _.each($scope.alertParameters, function(p) {
                if (p.name === param) {
                    _.extend(p, $scope.parentAlertDefinition.parameters[param]);
                };
            });
        };

        // Show Markdown preview
        $scope.showPreview = function() {
            $scope.showDescriptionPreview = !$scope.showDescriptionPreview;
        };

        // Verify if a property is being inherited from the parent alert
        $scope.isInheriting = function(p) {
            if ($scope.oProps.indexOf(p) === -1) {
                return true;
            }
            return false;
        };

        // Verify if a parameter is being inherited from the parent alert
        $scope.paramIsInheriting = function(p) {
            if ($scope.oParams.indexOf(p) === -1 && $scope.alertDefinition.parent_id && $scope.parentAlertDefinition.parameters && $scope.parentAlertDefinition.parameters[p]) {
                return true;
            }
            return false;
        };

        // Verify if a parameter is present in the parent alert
        $scope.paramIsInParent = function(p) {
            if ($scope.alertDefinition.parent_id && $scope.parentAlertDefinition.parameters && $scope.parentAlertDefinition.parameters[p]) {
                return true;
            }
            return false;
        };

        // Check wether a property is overwritten or inherited from parent alert
        $scope.isOverwritten = function(p) {
            if ($scope.oProps.indexOf(p) !== -1 && ($scope.mode == 'inherit' ||
                ($scope.alertDefinition && $scope.alertDefinition.parent_id))) {
                    return true;
            }
            return false;
        };

        // Validate a parameter's name to be a valid python variable name
        $scope.paramNameIsValid = function(name) {
            var re = /^[_a-zA-Z][_a-zA-Z0-9]*/;
            return re.test(name);
        };

        $scope.dateOptions = {
            formatYear: 'yy',
            startingDay: 1
        };

        $scope.format = 'dd.MM.yyyy';

        // One-time set of the entityFilter.formEntityFilters and entityFilter.textEntityFilters when the alert definition arrives from backend
        $scope.$watch('alertDefinition', function() {
            if ($scope.alertDefinition !== null) {
                $scope.resetEntityFilter();
                $scope.resetEntityExcludeFilter();
                $scope.resetNotifications();
            }
        });

        // If entity filter input method is 'form', reflect changes of entityFilter.formEntityFilters on entityFilter.textEntityFilters
        $scope.$watch('entityFilter.formEntityFilters', function() {
            if ($scope.entityFilterInputMethod === 'form') {
                // Process a copy so we safely remove $$hashKey property which we don't want to be transfered to entityFilter.textEntityFilters
                var formEntityFiltersClone = angular.copy($scope.entityFilter.formEntityFilters);
                for (var p in formEntityFiltersClone) {
                    if (formEntityFiltersClone.hasOwnProperty(p) && p === '$$hashKey') {
                        delete formEntityFiltersClone[p];
                    }
                }
                $scope.entityFilter.textEntityFilters = JSON.stringify(formEntityFiltersClone, null, $scope.INDENT);
            }
        }, true);

        // Same as above, but for excluded entities.
        $scope.$watch('entityExcludeFilter.formEntityFilters', function() {
            if ($scope.entityExcludeFilterInputMethod === 'form') {
                var formEntityFiltersClone = angular.copy($scope.entityExcludeFilter.formEntityFilters);
                for (var p in formEntityFiltersClone) {
                    if (formEntityFiltersClone.hasOwnProperty(p) && p === '$$hashKey') {
                        delete formEntityFiltersClone[p];
                    }
                }
                $scope.entityExcludeFilter.textEntityFilters = JSON.stringify(formEntityFiltersClone, null, $scope.INDENT);
            }
        }, true);

        // If entity filter input method is 'text', reflect changes of entityFilter.textEntityFilters on entityFilter.formEntityFilters
        $scope.$watch('entityFilter.textEntityFilters', function() {
            if ($scope.entityFilterInputMethod === 'text') {
                try {
                    var parsedJson = JSON.parse($scope.entityFilter.textEntityFilters);
                    $scope.entityFilter.formEntityFilters = parsedJson;
                    $scope.invalidFormat = false;
                } catch (ex) {
                    $scope.invalidFormat = true;
                }
            }
        }, true);

        // Same as above, for excluded entities.
        $scope.$watch('entityExcludeFilter.textEntityFilters', function() {
            if ($scope.entityExcludeFilterInputMethod === 'text') {
                try {
                    var parsedJson = JSON.parse($scope.entityExcludeFilter.textEntityFilters);
                    $scope.entityExcludeFilter.formEntityFilters = parsedJson;
                    $scope.invalidFormat = false;
                } catch (ex) {
                    $scope.invalidFormat = true;
                }
            }
        }, true);

        // Deep copy an alert into a new object
        var extendAlert = function(src) {
            var n = _.extend({}, src);
            if (src.entities) {
                n.entities = angular.copy(src.entities);
            }
            if (src.entities_exclude) {
                n.entities_exclude = angular.copy(src.entities_exclude);
            }
            if (src.notifications) {
                n.notifications = angular.copy(src.notifications);
            }
            return n;
        };

        /** The getEntityProperties() returns an object with the data to populate the directives that represent the entity filter forms
         * We transform it to be an array of objects, one object per entity filter type with keys: "type" + keys that correspond to each filter type
         * E.g. [ {"type": "zomcat", "environment": "..", "project": "..", ...}, {"type": "host", "external_ip": "..", ...}, ... ]
         */
        CommunicationService.getEntityProperties().then(
            function(data) {
                for (var p in data) {
                    if (data.hasOwnProperty(p)) {
                        var nextFilterType = {};
                        nextFilterType.type = p;
                        angular.extend(nextFilterType, data[p]);
                        $scope.entityFilter.types.push(nextFilterType);
                        $scope.entityExcludeFilter.types.push(nextFilterType);
                    }
                }

                // Sort entity filter types.
                $scope.entityFilter.types = _.sortBy($scope.entityFilter.types, "type");
                $scope.entityExcludeFilter.types = _.sortBy($scope.entityExcludeFilter.types, "type");
            }
        );

        // Get all available tags
        CommunicationService.getAllTags().then(
            function(data) {
                $scope.allTags = data;
            }
        );

        MainAlertService.removeDataRefresh();

        // Determine controller actions based on mode.

        // Add mode
        if ($scope.checkDefinitionId) {
            $scope.mode = 'add';
            $scope.defaultTeam = userInfo.teams.split(',')[0];
            $scope.defaultRespTeam = $scope.defaultTeam;
            $scope.defaultEntitiesFilter = [];
            $scope.defaultEntitiesExcludeFilter = [];
            $scope.defaultNotifications = [];
            return $scope.getCheckDefinition();
        }

        // Edit mode
        if ($scope.alertDefinitionId) {
            $scope.mode = 'edit';
            return $scope.getAlertDefinition($scope.alertDefinitionId);
        }

        // Inherit mode
        if ($scope.parentAlertDefinitionId) {
            $scope.mode = 'inherit';
            return $scope.getParentAlertDefinition($scope.parentAlertDefinitionId, function() {
                $scope.checkDefinitionId = $scope.parentAlertDefinition.check_definition_id;
                $scope.getCheckDefinition();
                $scope.alertDefinition = extendAlert($scope.parentAlertDefinition);
                $scope.alertDefinition.template = false;
                if ($scope.parentAlertDefinition.entities == null) {
                    $scope.defaultEntitiesFilter = [];
                    $scope.markAsOverwritten('entities');
                }
                if ($scope.parentAlertDefinition.entities_exclude == null) {
                    $scope.defaultEntitiesExcludeFilter = [];
                    $scope.markAsOverwritten('entities_exclude');
                }
                if ($scope.parentAlertDefinition.notifications == null) {
                    $scope.defaultNotifications = [];
                    $scope.markAsOverwritten('notifications');
                }
                _.each($scope.parentAlertDefinition.parameters, function(p, name) {
                    if ($scope.oParams.indexOf(name) === -1) {
                        $scope.alertParameters.push(_.extend({"name": name}, p));
                        $scope.alertDefinition.parameters[name] = p;
                    }
                });
            });
        }

        // Clone mode
        if ($scope.cloneFromAlertDefinitionId) {
            $scope.mode = 'clone';
            $scope.getAlertDefinition($scope.cloneFromAlertDefinitionId, function() {
                delete $scope.alertDefinition.id;
                $scope.alertDefinition.team = userInfo.teams.split(',')[0] || '';
                var duplicateCount = 0;
                while (!CommunicationService.isValidAlertName($scope.alertDefinition.name)) {
                    duplicateCount++;
                    $scope.alertDefinition.name = $scope.alertDefinition.name + ' (' + duplicateCount + ')';
                }
            });
        }
    }
]);
