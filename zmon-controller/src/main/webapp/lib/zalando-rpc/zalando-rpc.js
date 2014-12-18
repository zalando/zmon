angular.module('zalandoRpc', []).
    /**
     * @service
     * @name $rpc
     *
     * @description
     * A factory which allows easy access to RPC-based webservices. For configuration of such a webservice in Java-applications
     * have a look at <code>de.zalando.angularjs.rpc.annotation.RPCService</code>.
     *
     * @param {String} basePath     The base-url to use for calls to the webservice. This should map to the value of
     *                              the @RPCService-annotation.
     * @param {Object} params       An object of default params to send with each request.
     * @param {Object} methods      An object of methods which are exported by the webservice. Every method has a configuration:
     *                              <ul>
     *                                  <li><b>hasEffects:</b> boolean, true if this method has any effect on the backend-state
     *                                      ("write access", not nullipotent), default: true</li>
     *                                  <li><b>repeatable:</b> boolean, true if this method can be repeated any times without
     *                                      additional modifications (idempotent), default: false</li>
     *                                  <li><b>isArray:</b> boolean, true if the result is an array and not an object, default:
     *                                      false</li>
     *                                  <li><b>params:</b> String[], names of the params in the order as the method is to be
     *                                      called, default: empty</li>
     *                              </ul>
     *
     * @returns {Promise}           A promise to react on success or failure. The data as returned from the webservice call is
     *                              automatically unpacked into the result, so that callbacks not always have to be given.
     *
     * @example
     * <pre>
     *     var FruitService = $rpc('/rpc/fruit',                       // make calls to /rpc/fruit/...
     *                            { 'basket': 23 },                    // always sent basket=23 with every request
     *                            {
     *                                'add': { 'params': ['name'] },   // modifying, non-repeatable method
     *                                                                 // POST request to /rpc/fruit/add
     *                                                                 // params as JSON-body
     *                                                                 // first param is sent as name
     *                                'list': { 'hasEffects': false,   // non-modifying (and repeatable) method
     *                                          'isArray': true }      // which returns an array of values
     *                                                                 // GET request to /rpc/fruit/list
     *                            });
     *
     *     var fruits;
     *     FruitService.add('apple').$then(function success() {        // service methods return a promise
     *             fruits = FruitService.list();                       // which is automatically unpacked, when the call returns
     *         });
     * </pre>
     */
    factory('$rpc', ['$http', '$q', function factory($http, $q) {
        function RPCService(basePath, params, methods) {
            this.methods = [];
            this.basePath = basePath;
            this.params = params;

            function bindInvoke(method) {
                return function () {
                    return method.invoke.apply(method, arguments);
                };
            }

            for (var name in methods) {
                var method = methods[name];

                this.methods[name] = new RPCMethod(this, name, method);
                this[name] = bindInvoke(this.methods[name]);
            }
        }

        function RPCMethod(service, name, method) {
            var path = service.basePath + '/' + name;
            var httpMethod = method.hasEffects === false ? 'GET' : (method.repeatable === true ? 'PUT' : 'POST');
            var hasBody = httpMethod !== 'GET';
            var isArray = method.isArray === true;
            var hasFile = false;

            var paramPositions = [];

            function init() {
                if (method.params) {
                    method.params.forEach(function (param) {
                        if (! angular.isObject(param)) {
                            param = {'name': param};
                        }

                        // if there is a file to transmit, we can only use POST
                        if (param.isFile) {
                            hasFile = true;
                            httpMethod = 'POST';
                            hasBody = true;
                        }

                        paramPositions.push(param);
                    });
                }
            }

            function buildResult(promise, isArray) {
                var result = [];
                if (! isArray) {
                    result = {};
                }

                result.$promise = promise;
                result.$loading = true;
                delete result.$error;

                promise.then(function (data) {
                    if (data) {
                        if (isArray) {
                            for (var i = 0; i < data.length; ++i) {
                                result.push(data[i]);
                            }
                        } else {
                            angular.extend(result, data);
                        }
                    }

                    delete result.$loading;
                }, function (error) {
                    delete result.$loading;
                    result.$error = error;
                });

                result.$then = function (success, failure, isArrayParam) {
                    if (isArrayParam === undefined) {
                        if (typeof failure === 'boolean') {
                            isArrayParam = failure;
                            failure = undefined;
                        } else {
                            isArrayParam = isArray;
                        }
                    }

                    function wrapped(handler, reject) {
                        return function (data) {
                            var result = handler(data);
                            if (result === undefined) {
                                result = data;
                            }

                            return reject ? $q.reject(result) : result;
                        };
                    }

                    var newPromise = failure ? promise.then(wrapped(success), wrapped(failure, true))
                            : promise.then(wrapped(success));
                    return buildResult(newPromise, isArrayParam);
                };

                return result;
            }

            this.invoke = function () {
                var params = {};
                var files = {};
                for (var i = 0; i < paramPositions.length && i < arguments.length; i++) {
                    var param = paramPositions[i];
                    if (param.isFile) {
                        files[param.name] = arguments[i];
                    } else {
                        params[param.name] = arguments[i];
                    }
                }

                var query;
                var body;

                if (hasFile) {
                    query = null;
                    body = new FormData();

                    // we append all "regular" data as one multipart-part named "data"
                    body.append('data', JSON.stringify(params));

                    for (var name in files) {
                        body.append(name, files[name]);
                    }
                } else if (hasBody) {
                    query = null;
                    body = params;
                } else {
                    query = params;
                    body = null;
                }

                var requestConfig = {method: httpMethod, url: path, params: query, data: body};
                if (hasFile) {
                    requestConfig.headers = {'Content-Type': undefined}; // make the browser set content-type and multipart-boundary
                    requestConfig.transformRequest = function(data) { return data; }; // actually use the provided FormData
                }

                var results = [];
                var request = $http(requestConfig).then(function (data) {
                    for (var i = 0; i < results.length; i++) {
                        var result = results[i];

                        if (isArray) {
                            for (var j = 0; j < data.data.length; j++) {
                                result.push(data.data[j]);
                            }
                        } else {
                            angular.copy(data.data, result);
                        }
                    }

                    return data.data;
                }, function (error) {
                    var data = error.data;
                    data.status = error.status;

                    return $q.reject(data);
                });

                return buildResult(request, isArray);
            };

            init();
        }

        return function (basePath, params, methods) {
            return new RPCService(basePath, params, methods);
        };
    }]);

/**
 * allow to still include the module by it's old name.
 */
angular.module('z-rpc', ['zalandoRpc']);
