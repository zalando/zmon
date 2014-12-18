<%@ taglib prefix="c" uri="http://java.sun.com/jsp/jstl/core" %>

<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge,chrome=1">
    <title>ZMON 2.0</title>

    <link rel="stylesheet" type="text/css" href="asset/css/zalando-bootstrap.css?t=${buildTime}" />
    <link rel="stylesheet" type="text/css" href="styles/main.css" />
    <link rel="stylesheet" type="text/css" href="styles/charts.css" />
    <link rel="stylesheet" type="text/css" href="styles/dashboard.css" />
    <link rel="stylesheet" type="text/css" href="styles/errors.css" />
    <link rel="stylesheet" type="text/css" href="styles/forms.css" />

    <script src="lib/piwik/piwik.min.js?time=${buildTime}" charset="utf-8"></script>

</head>
<body>

    <nav class="navbar navbar-inverse" role="navigation" id="navi">
        <div class="navbar-header">
            <a class="navbar-brand" href="/#/">ZMON 2.0</a>
        </div>
    </nav>

    <div id="main">
        <div class="container">
            <form class="form-signin" action="<%= request.getContextPath() %>/login" method="post">
                <h2 class="form-signin-heading">Please sign in</h2>
                <% if (request.getAttribute("error") != null || request.getParameter("error") != null) { %>
                    <div class="alert alert-warning" ng-if="errorMessage">
                        <i class="fa fa-fw fa-warning"></i>
                        <% if ("session_expired".equals(request.getParameter("error"))) { %>
                            Session expired
                        <% } else if ("403".equals(request.getParameter("error"))) { %>
                            Sorry, but you don't have the rights to access this application (403)
                        <% } else { %>
                            Login failed
                        <% } %>
                    </div>
                <% } %>
                <input name="j_username" type="text" class="form-control" placeholder="Username (LDAP)" required="" autofocus="">
                <input name="j_password" type="password" class="form-control" placeholder="Password" required="">
                <input name="next_page" type="hidden" value="<c:out value="${param.next_page}"/>">
                <button class="btn btn-lg btn-primary btn-block" type="submit">Sign in</button>
            </form>
        </div>
    </div>
</body>
</html>
