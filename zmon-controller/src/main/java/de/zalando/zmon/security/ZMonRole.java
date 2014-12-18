package de.zalando.zmon.security;

public enum ZMonRole {

    ADMIN("ZMON_ADMIN"),
    LEAD("ZMON_LEAD"),
    USER("ZMON_USER"),
    VIEWER("ZMON_VIEWER"),
    API_READER("ZMON_API_READER"),
    API_WRITER("ZMON_API_WRITER");

    private final String roleName;

    private ZMonRole(final String roleName) {
        this.roleName = roleName;
    }

    public String getRoleName() {
        return roleName;
    }

    @Override
    public String toString() {
        return roleName;
    }
}
