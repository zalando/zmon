angular.module('zmon2App').directive('trend', function() {
    return {
        restrict: 'E',
        scope: {
            title: '@title',
            mean: '=mean',
            current: '=current'
        },
        template: '<span class="trend-arrow"><i class="fa fa-location-arrow"></i></span>',
        replace: true,
        link: function(scope, elem, attrs) {
            /* Given a rotation of the arrow in degrees, calculates the color.
             * Returned color is between total red (255,0,0) for rotation -90deg (arrow vertically up)
             * and total green (0.255,0) for rotation 90deg (arrow vertically down). Blue is always 0 for our gradient.
             * 0deg is arrow pointing horizontally towards the right and corresponds to total yello (255,255,0)
             * For each degree of rotation, there is normally a 2.83 color shift. But to cause more visible color changes it is pumped up by a certain factor.
             * We start @ yellow (255,255,0) for 0deg rotation.
             * Positive degrees mean it's a colorRed decrease. Negative degrees mean it's a colorGreen decrease.
             */
            function calcColor(rot) {
                var COLOR_SHIFT_FACTOR = 4,
                    colorRed = 255,
                    colorGreen = 255,
                    colorShift = parseInt(rot * COLOR_SHIFT_FACTOR, 10);

                if (rot >= 0) {
                    colorRed = _.max([0, colorRed - colorShift]);
                } else {
                    colorGreen = _.max([0, colorGreen + colorShift]);
                }
                var finalColor = ("0" + colorRed.toString(16)).slice(-2) + ("0" + colorGreen.toString(16)).slice(-2) + '00';
                if (finalColor.match(/[0-9a-f]{6}/)) {
                    return finalColor;
                }
                console.error('INVALID FINAL COLOR: ', finalColor, ' FOR ROTATION: ', rot);
                return '000000';
            }
            scope.$watch('current', function() {
                var rot = 90 * (scope.mean - scope.current) / Math.max(1, scope.mean),
                    newColor = null;
                if (isNaN(rot)) {
                    return;
                }
                rot = _.max([-90, _.min([90, rot])]);
                newColor = calcColor(rot);
                // Font awesome icon fa-location-arrow is already @45 degrees; adjust accordingly;
                elem[0].style.webkitTransform = 'rotate(' + (rot + 45) + 'deg)';
                elem[0].style.color = '#' + newColor;
            });
        }
    };
});