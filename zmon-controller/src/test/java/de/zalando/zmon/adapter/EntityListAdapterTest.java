package de.zalando.zmon.adapter;

import java.util.List;
import java.util.Map;

import org.junit.Assert;
import org.junit.Test;

import de.zalando.zmon.domain.Entities;

public class EntityListAdapterTest {

    private final EntityListAdapter adapter = new EntityListAdapter();

    @Test
    public void testUnmarshalNullEntity() throws Exception {
        final List<Map<String, String>> result = adapter.unmarshal(null);

        Assert.assertNotNull(result);
        Assert.assertTrue(result.isEmpty());
    }

    @Test
    public void testMarchalNullList() throws Exception {
        final Entities entities = adapter.marshal(null);

        Assert.assertNotNull(entities);
    }
}
