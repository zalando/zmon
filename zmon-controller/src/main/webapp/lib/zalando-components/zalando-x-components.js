(function () {
    function factory(module, Spinner, angular) {
        'use strict';

        /**
         * @module zalandoXComponents Angularmodule to inject in your app
         * @description
         * An angular module to keep all Zalando built directives. There will be two modules zalando-components and zalando-x-components.
         * zalando-components will only hold stable directives which fit all our need.
         * zalando-x-components will hold all directives we want to test more before we finalize it. This is some kind of "beta" or "pre-stage" module.
         *
         * There is also one css file (zalando-components.css and zalando-x-components.css) generated for each module which includes all styles related to directives.
         *
         * @example
         * <link rel="stylesheet" type="text/css" href="/asset/css/zalando-x-components.css?time=${buildTime}"/>
         * <script src="lib/zalando-components/zalando-x-components.js" type="text/javascript"></script>
         *
         */
        module.run(['$rootScope', function init($rootScope) {
                $rootScope.constructor.prototype.$relayout = function $relayout() {
                        this.$broadcast('$relayout');
                    };
            }]);


        /**
         * allow to load by it's old name.
         */
        angular.module('zalando-x-components', ['zalandoXComponents']);

        /**
         *
         * @directive
         * @name zxLoading
         *
         * @description
         * The module zalando-x-components.loading offers a directive to display a loading indicator.
         * It makes use of spin.js which has to be included with a classic <script> tag or requirejs.
         *   <script src="lib/directives/spin.js" type="text/javascript"></script>
         *
         * The directive itself can be used an attribute to the container which should hold the indicator.
         * The Controller should have a $scope.loading variable which indicates whether to show or not to show the spinner.
         *
         * @attribute zxLoading
         * @value {boolean} loading
         *
         * @exampleInView
         * In your html use it like this. {{ loading }} is a reference to a boolean scope variable.
         * <pre>
         *     <div ng-controller="myController" zx-loading="{{loading}}">
         * </pre>
         *
         * @exampleInController
         * In your controller use it like this.
         * <pre>
         *      // Initialize with false, to not display the indicator.
         *      $scope.loading = false;
         *
         *      $scope.open = function() {
         *          //when we start our request we set loading to true, the indicator is being displayed.
         *          $scope.loading = true;
         *          $scope.resultArray = undefined;
         *
         *          // In the success or error callbacks we set the loading variable to false to disable the indicator.
         *          Service.list({param1: null, param2: null}, function(response) {
         *              $scope.resultArray = response;
         *              $scope.loading = false;
         *          }, function(errorResponse){
         *               console.log("we got an error while fetching our result.");
         *              $scope.loading = false;
         *          });
         *      };
         * </pre>
         *
         */
        module.directive('zxLoading', ['$compile', '$timeout', function($compile, $timeout) {
            return {
                restrict: 'A',
                scope: false,
                link: function(scope, elem, attrs) {
                    // if loaded without require.js, Spinner might not be known so far, lets try to get it from
                    // global scope then!
                    if (! Spinner) {
                        Spinner = window.Spinner;
                    }

                    scope = scope.$new(true);

                    elem.addClass('loading-container');
                    var target = $compile('<div class=\"indicator\" ng-show=\"loading\"></div>')(scope);
                    elem.append(target);
                    target = target.get(0); // need the dom-element

                    var opts = {
                        lines: 11, // The number of lines to draw
                        length: 4, // The length of each line
                        width: 3, // The line thickness
                        radius: 6, // The radius of the inner circle
                        corners: 1, // Corner roundness (0..1)
                        rotate: 0, // The rotation offset
                        direction: 1, // 1: clockwise, -1: counterclockwise
                        color: '#000', // #rgb or #rrggbb
                        speed: 1, // Rounds per second
                        trail: 60, // Afterglow percentage
                        shadow: false, // Whether to render a shadow
                        hwaccel: false, // Whether to use hardware acceleration
                        className: 'spinner', // The CSS class to assign to the spinner
                        zIndex: 2e9, // The z-index (defaults to 2000000000)
                        top: 'auto', // Top position relative to parent in px
                        left: 'auto' // Left position relative to parent in px
                    };
                    var spinner = new Spinner(opts);

                    var position = false;
                    function startSpinner() {
                        if (scope.loading) {
                            // for some reason the positioning sometimes does not really work, so we'll just do it here
                            var noSize = elem.height() === 0 || elem.width() === 0;
                            if (!noSize) {
                                opts.top = elem.height() / 2 - opts.radius - opts.length;
                                opts.left = elem.width() / 2 - opts.radius - opts.length;

                                if (! position || position.top !== opts.top || position.left !== opts.left) {
                                    position = {
                                        top: opts.top,
                                        left: opts.left
                                    };
                                    spinner.spin(target);
                                }
                            }

                            $timeout(startSpinner, 100);
                        }
                    }

                    function stopSpinner() {
                        position = false;
                        spinner.stop();
                    }

                    attrs.$observe('zxLoading', function(loading) {
                        scope.loading = loading === 'true';
                        if (scope.loading) {
                            startSpinner();
                        } else {
                            stopSpinner();
                        }
                    });

                    scope.$on('$destroy', function () {
                        stopSpinner();
                    });

                    function relayout() {
                        if (scope.loading) {
                            startSpinner();
                        }
                    }
                    scope.$on('relayout', function() {
                            console.warn('using "relayout" is deprecated, please use "$relayout" instead!');
                            relayout();
                        });
                    scope.$on('$relayout', relayout);
                }
            };
        }]);
    }

    if (typeof require === 'function' && typeof require.specified === 'function' &&
            require.specified('zalandoXComponentsModule')) {
        // loaded using require.js

        define(['zalandoXComponentsModule', 'spin', 'angular'], factory);
    } else {
        // loaded directly

        console.warn('loading js-files without require.js is deprecated!');

        var module = angular.module('zalandoXComponents', []);
        var spin = false; // possibly just not known yet!

        factory(module, spin, angular);
    }
})();
