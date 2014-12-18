var GAUGE_LAST_ID = 0;
angular.module('zmon2App').directive('gauge', function() {
    return {
        restrict: 'E',
        scope: {
            title: '@title',
            value: '=value',
            max: '=max',
            options: '=options'
        },
        link: function(scope, elem, attrs) {
            GAUGE_LAST_ID++;
            var gaugeId = GAUGE_LAST_ID;
            elem.append('<div class="gauge-wrapper" id="gauge-' + gaugeId + '"></div>');

            var g = null;

            var options = {min: 0, max: null, reverse: false};

            if (typeof scope.options !== 'undefined') {
                _.extend(options, scope.options);
            }
            var colors = ['#78B924', '#ebb129', '#ebb129', '#dd3010'];

            if (options.reverse) {
                colors.reverse();
            }

            scope.$watch('value', function(newVal, oldVal) {
                if (isNaN(newVal)) {
                    console.warn(new Date(), "Gauge value is not a number: ", newVal);
                } else {
                    scope.value = parseFloat(scope.value);

                    // Till we iron out all error possibilities with stacktrace, let's use a try catch.
                    try {
                        if (g === null) {
                            g = new JustGage({
                                id: "gauge-" + gaugeId,
                                value: scope.value.toFixed(1),
                                min: options.min,
                                gaugeColor: '#7f7f7f',
                                max: options.max === null ? scope.max.toFixed(1) : options.max,
                                title: " ",
                                valueFontColor: '#fff',
                                showInnerShadow: true,
                                shadowOpacity: 0.8,
                                shadowSize: 4,
                                shadowVerticalOffset: 2,
                                levelColors: colors
                            });
                        } else {
                            if (options.max === null) {
                                var newMax = scope.max.toFixed(1);
                                g.config.max = newMax;
                                g.txtMax.attr('text', newMax);
                            }
                            g.refresh(scope.value.toFixed(1));
                        }
                    } catch (ex) {
                        console.error("ERROR Gauge:", ex);
                    }
                }
            });
        }
    };
});
