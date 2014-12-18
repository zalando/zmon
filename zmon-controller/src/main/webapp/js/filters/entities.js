angular.module('zmon2App').filter('entities', function() {
    /*
     * Given a definition's entities filter, which is in format [{COND_1},{COND_2}], where COND_x are connected via "OR"
     * and the properties inside the COND_x object are connected via "AND", it returns a slghtly more readable  HTML representation
     * of the entities filter components
     * NOTE: excludes null values and the key "$$hashKey"
     */
    return function(entities) {
        var conditions = [];
        _.each(entities, function(map) {
            var arr = [];
            _.each(map, function(value, key) {
                if (value !== null && key !== '$$hashKey') {
                    arr.push(_.escape(key) + '&thinsp;=&thinsp;' + _.escape(value));
                }
            });
            arr.sort();
            conditions.push(arr.join(' <b>AND</b> '));
        });
        conditions.sort();

        return '<div class="entities">' + conditions.join('<i>OR</i> ') + '</div>';
    };
});
