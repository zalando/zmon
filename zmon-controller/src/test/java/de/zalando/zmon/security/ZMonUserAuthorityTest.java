package de.zalando.zmon.security;

import org.junit.Assert;
import org.junit.Test;

import com.google.common.collect.ImmutableSet;

import de.zalando.zmon.domain.AlertComment;
import de.zalando.zmon.domain.AlertDefinition;
import de.zalando.zmon.domain.Dashboard;
import de.zalando.zmon.domain.DefinitionStatus;
import de.zalando.zmon.domain.EditOption;

public class ZMonUserAuthorityTest {

    @Test
    public void testDeleteOwnComment() {
        final ZMonUserAuthority authority = new ZMonUserAuthority("foo", ImmutableSet.<String>of());

        final AlertComment toDelete = new AlertComment();
        toDelete.setCreatedBy("foo");

        Assert.assertTrue(authority.hasDeleteCommentPermission(toDelete));
    }

    @Test
    public void testDeleteUserComment() {

        final ZMonUserAuthority authority = new ZMonUserAuthority("foobar", ImmutableSet.<String>of());

        final AlertComment toDelete = new AlertComment();
        toDelete.setCreatedBy("foo");

        Assert.assertFalse(authority.hasDeleteCommentPermission(toDelete));
    }

    @Test
    public void testEditOwnDashboard() {
        final ZMonUserAuthority authority = new ZMonUserAuthority("foo", ImmutableSet.<String>of());

        final Dashboard toEdit = new Dashboard();
        toEdit.setEditOption(EditOption.PRIVATE);
        toEdit.setCreatedBy("foo");

        Assert.assertTrue(authority.hasEditDashboardPermission(toEdit));
    }

    @Test
    public void testEditUserDashboard() {
        final ZMonUserAuthority authority = new ZMonUserAuthority("foobar", ImmutableSet.<String>of());

        final Dashboard toEdit = new Dashboard();
        toEdit.setEditOption(EditOption.PRIVATE);
        toEdit.setCreatedBy("foo");

        Assert.assertFalse(authority.hasEditDashboardPermission(toEdit));
    }

    @Test
    public void testEditAlertDefinitionWithSameTeam() {
        final ZMonUserAuthority authority = new ZMonUserAuthority("foobar", ImmutableSet.of("Platform/Software"));

        final AlertDefinition toEdit = new AlertDefinition();
        toEdit.setTeam("PLATFORM/SOFTWARE");
        toEdit.setResponsibleTeam("Platform/System");
        toEdit.setStatus(DefinitionStatus.ACTIVE);

        Assert.assertTrue(authority.hasEditAlertDefinitionPermission(toEdit));
    }

    @Test
    public void testEditInactiveAlertDefinitionWithSameResponsibleTeam() {
        final ZMonUserAuthority authority = new ZMonUserAuthority("foobar", ImmutableSet.of("Platform/System"));

        final AlertDefinition toEdit = new AlertDefinition();
        toEdit.setTeam("PLATFORM/SOFTWARE");
        toEdit.setResponsibleTeam("Platform/System");
        toEdit.setStatus(DefinitionStatus.INACTIVE);

        Assert.assertTrue(authority.hasEditAlertDefinitionPermission(toEdit));
    }

    @Test
    public void testEditActiveAlertDefinitionWithSameResponsibleTeam() {
        final ZMonUserAuthority authority = new ZMonUserAuthority("foobar", ImmutableSet.of("Platform/System"));

        final AlertDefinition toEdit = new AlertDefinition();
        toEdit.setTeam("PLATFORM/SOFTWARE");
        toEdit.setResponsibleTeam("Platform/System");
        toEdit.setStatus(DefinitionStatus.ACTIVE);

        Assert.assertFalse(authority.hasEditAlertDefinitionPermission(toEdit));
    }

    @Test
    public void testEditAlertDefinitionDifferentTeam() {
        final ZMonUserAuthority authority = new ZMonUserAuthority("foobar", ImmutableSet.of("Backend/Order"));

        final AlertDefinition toEdit = new AlertDefinition();
        toEdit.setTeam("Backend");
        toEdit.setResponsibleTeam("Backend/Article");
        toEdit.setStatus(DefinitionStatus.ACTIVE);

        Assert.assertFalse(authority.hasEditAlertDefinitionPermission(toEdit));
    }

    @Test
    public void testEditAlertDefinitionPrefix() {
        final ZMonUserAuthority authority = new ZMonUserAuthority("foobar", ImmutableSet.of("Backend"));

        final AlertDefinition toEdit = new AlertDefinition();
        toEdit.setTeam("Backend/Order");
        toEdit.setResponsibleTeam("Platform/Database");
        toEdit.setStatus(DefinitionStatus.ACTIVE);

        Assert.assertTrue(authority.hasEditAlertDefinitionPermission(toEdit));
    }

}
