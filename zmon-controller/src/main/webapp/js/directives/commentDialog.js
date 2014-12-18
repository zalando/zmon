var commentDialog = function(MainAlertService, UserInfoService, epochToDate) {
    return {
        restrict: 'E',

        scope: {
            uid: '=', // Unique identifier of comments topic
            label: '@', // Text of label which will be added beside comment icon
            entity: '=', // Additional parameter in future plane is to create mechanism for handling optional parameters
            indicator: '=?', // Show number of comments
            update: '=?', // Force update of comments
            limit: '=?', // Maximum number of comments
            offset: '=?', // Number of skipped comments
            data: '=?', // Prefetched comments which will be displayed by default (recommendation is to left this parameter empty)
            save: '&', // Function which provide insert functionality
            delete: '&', // Function which provide delete functionality
            load: '&' // Function which loading comments
        },

        link: function(scope, element, attributes) {
            // Basic modal settings
            var modal = element.find('.modal').modal({
                show: false,
                keyboard: true,
                backdrop: false
            });

            // Getting all available information about user
            scope.userInfo = UserInfoService.get();

            //Checking the limit and offset and assigning default values
            scope.limit = scope.limit || 5;
            scope.offset = scope.offset || 0;

            // TODO: Improve adding of mandatory and optional information to comment object
            scope.defaultComment = {
                alert_definition_id: scope.uid
            };

            if (scope.entity) scope.defaultComment.entity_id = scope.entity;

            scope.comment = angular.copy(scope.defaultComment);

            // Checking the length of prefetched comments array (if exist) and slicing to fulfill limit value
            if(scope.data) {
                scope.comments = scope.data.slice(0, scope.limit);
                scope.allLoaded = scope.data.length <= scope.limit;
                scope.counter = ' (' + scope.comments.length + (scope.allLoaded ? '' : '+') + ')';
            }

            // Opening dialog
            scope.openDialog = function() {
                modal.modal('show');
            };

            // Closing dialog
            scope.closeDialog = function() {
                modal.modal('hide');
            };

            // Loading more comments after click on "More comments" button and appending to current comments
            scope.loadComments = function() {
                scope.offset += scope.limit;
                scope.load({
                    id: scope.uid,
                    limit: scope.limit + 1,
                    offset: scope.offset,
                    cb: function(response) {
                        var comments = response.slice(0, scope.limit);
                        scope.allLoaded = response.length <= scope.limit;
                        scope.comments = _.uniq(comments.concat(scope.comments), false, function(item) { return item.id; });
                        scope.counter = ' (' + scope.comments.length + (scope.allLoaded ? '' : '+') + ')';
                    }
                });
            };

            // Inserting comment and appending to list of comments
            scope.addComment = function() {
                if (scope.form.$valid) {
                    scope.save({
                        comment: scope.comment,
                        cb: function(comment) {
                            scope.comments = [comment].concat(scope.comments);
                            scope.comment = angular.copy(scope.defaultComment);
                            scope.counter = ' (' + scope.comments.length + (scope.allLoaded ? '' : '+') + ')';
                        }
                    });
                }
            };

            // Deleting comment
            scope.removeComment = function(id) {
                scope.delete({
                    id: id,
                    cb: function() {
                        scope.offset--;
                        scope.comments = scope.comments.filter(function(comment) {
                            return comment.id != id;
                        });
                        scope.counter = ' (' + scope.comments.length + (scope.allLoaded ? '' : '+') + ')';
                    }
                });
            };

            // Removing additional parameter entity which represents entity flag in comment
            scope.removeEntity = function() {
                delete scope.defaultComment.entity_id;
                delete scope.comment.entity_id;
                delete scope.entity;
            };

            // Helper function which showing the last inserted comment
            scope.scrollToLastComment = function() {
                var commentsContainer = element.find('.modal-body');
                commentsContainer.scrollTop(commentsContainer.prop('scrollHeight'));
            };

            // Triggering scrollToLastComment after each new comment
            scope.$watch('comments', function(comments, prev) {
                if(comments && prev &&  comments.length - 1 === prev.length) scope.scrollToLastComment();
            });

            scope.$watch('data', function(data, prev) {
                if(!data) return;
                scope.comments = data.slice(0, scope.limit);
                scope.allLoaded = data.length <= scope.limit;
                scope.counter = ' (' + scope.comments.length + (scope.allLoaded ? '' : '+') + ')';
            });

            // Synchronization of UID change
            scope.$watch('uid', function(uid) {
                scope.defaultComment.alert_definition_id = uid;
                scope.comment = angular.copy(scope.defaultComment);
            });

            // Listening for open event of modal
            // When modal is open fetch comments (if they are not prefetched) and stop auto refreshing
            modal.on('show.bs.modal', function() {
                if(scope.update || !scope.data) {
                    scope.offset = 0;

                    scope.load({
                        id: scope.uid,
                        limit: scope.limit + 1,
                        offset: scope.offset,
                        cb: function(response) {
                            scope.comments = response.slice(0, scope.limit);
                            scope.allLoaded = response.length <= scope.limit;
                            scope.counter = ' (' + scope.comments.length + (scope.allLoaded ? '' : '+') + ')';
                        }
                    });
                }

                setTimeout(function() {
                    element.find('textarea').focus();
                }, 0);

                MainAlertService.pauseDataRefresh();
            });

            // Listening for open event of modal and when modal is closed resume auto refreshing
            modal.on('hide.bs.modal', function() {
                scope.counter = ' (' + (scope.comments.length < scope.limit ? scope.comments.length : scope.limit + '+') + ')';
                MainAlertService.resumeDataRefresh();
            });

        },

        templateUrl: 'templates/comments.html'
    };
};

angular.module('zmon2App').directive('commentDialog', ['MainAlertService', 'UserInfoService', commentDialog]);