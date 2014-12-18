package de.zalando.zmon.rest;

import de.zalando.zmon.service.GroupService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.*;

import java.util.List;

/**
 * Created by jmussler on 11/11/14.
 */

/**
 * curl -v -X PUT --user jmussler: 'http://localhost:33400/rest/api/v1/groups/pf-software/active/alfredo.valles@zalando.de'
 * curl -v --user jmussler: 'http://localhost:33400/rest/api/v1/groups'
 */


@Controller
@RequestMapping("/api/v1/groups")
public class GroupApi {

    private final GroupService groupService;

    @Autowired
    public GroupApi(final GroupService groupService) {
        this.groupService = groupService;
    }

    @RequestMapping(method = RequestMethod.GET)
    @ResponseStatus(HttpStatus.OK)
    @ResponseBody
    public List<ZmonGroup> list() {
        return groupService.getAllGroups();
    }

    @ResponseStatus(HttpStatus.OK)
    @ResponseBody
    @RequestMapping(value = "/{id}/member/{member}/", method = RequestMethod.PUT)
    public long addMember(@PathVariable("id") final String id, @PathVariable("member") final String member) {
        return groupService.addMember(id, member);
    }

    @ResponseStatus(HttpStatus.OK)
    @ResponseBody
    @RequestMapping(value = "/{id}/member/{member}/", method = RequestMethod.DELETE)
    public long removeMember(@PathVariable("id") final String id, @PathVariable("member") final String member) {
        return groupService.removeMember(id, member);
    }

    @ResponseStatus(HttpStatus.OK)
    @ResponseBody
    @RequestMapping(value = "/{id}/active/{member}/", method = RequestMethod.PUT)
    public long addActive(@PathVariable("id") final String id, @PathVariable("member") final String member) {
        return groupService.addToActive(id, member);
    }

    @ResponseStatus(HttpStatus.OK)
    @ResponseBody
    @RequestMapping(value = "/{id}/active/{member}/", method = RequestMethod.DELETE)
    public long removeActive(@PathVariable("id") final String id, @PathVariable("member") final String member) {
        return groupService.removeFromActive(id, member);
    }

    @ResponseStatus(HttpStatus.OK)
    @ResponseBody
    @RequestMapping(value = "/{id}/active", method = RequestMethod.DELETE)
    public long clearActive(@PathVariable("id") final String id) {
        return groupService.clearActive(id);
    }

    @ResponseStatus(HttpStatus.OK)
    @ResponseBody
    @RequestMapping(value = "/{memberId}/phone/{phone}", method = RequestMethod.PUT)
    public long addPhone(@PathVariable("memberId") final String memberId, @PathVariable("phone") final String phone) {
        return groupService.addPhone(memberId, phone);
    }

    @ResponseStatus(HttpStatus.OK)
    @ResponseBody
    @RequestMapping(value = "/{memberId}/phone/{phone}", method = RequestMethod.DELETE)
    public long removePhone(@PathVariable("memberId") final String memberId, @PathVariable("phone") final String phone) {
        return groupService.removePhone(memberId, phone);
    }

    @ResponseStatus(HttpStatus.OK)
    @ResponseBody
    @RequestMapping(value = "/{memberId}/name/{name}", method = RequestMethod.PUT)
    public void setMemberName(@PathVariable("memberId") final String memberId, @PathVariable("name") final String name) {
        groupService.setName(memberId, name);
    }

    @ResponseStatus(HttpStatus.OK)
    @ResponseBody
    @RequestMapping(value = "/member/{memberId}/", method = RequestMethod.GET)
    public ZmonGroupMember getMember(@PathVariable("memberId") final String memberId) {
        return groupService.getMember(memberId);
    }
}
