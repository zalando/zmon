angular.module('zmon2App').directive('infiniteScroll', ['$location', 'APP_CONST',
    function ($location, APP_CONST) {
        return {
            scope: {
                visibleItemCount: "=",
                getTotalItemCount: "&"
            },
            link: function (scope, elem, attr) {
                function incrementVisibleItemCount() {
                    if (scope.visibleItemCount <= scope.getTotalItemCount()) {
                        scope.visibleItemCount = parseInt(scope.visibleItemCount) + APP_CONST.INFINITE_SCROLL_VISIBLE_ENTITIES_INCREMENT;
                    }
                }

                var debouncedIncrementVisibleItemCount = _.debounce(incrementVisibleItemCount, 2000, true);

                function scrollToBottomCallback() {
                    // Detect when nearing the bottom, and increment the visible entities
                    if ($(window).scrollTop() + $(window).height() > $(document).height() - 50) {
                        debouncedIncrementVisibleItemCount();
                    }
                }

                scope.visibleItemCount = parseInt(scope.visibleItemCount, 10);
                $(window).scroll(scrollToBottomCallback);
            }
        };
    }
]);
