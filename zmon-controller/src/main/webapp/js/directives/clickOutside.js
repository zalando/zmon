angular.module("zmon2App").directive('clickOutside', function($document){
    return {
        restrict: 'A',
        link: function(scope, elem, attr, ctrl) {
            elem.bind('click', function(e) {
                e.stopPropagation();
            });
            $document.bind('click', function() {
                scope.$apply(attr.clickOutside);
            })
        }
    }
});
