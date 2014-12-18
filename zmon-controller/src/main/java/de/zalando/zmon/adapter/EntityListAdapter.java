package de.zalando.zmon.adapter;

import java.util.LinkedList;
import java.util.List;
import java.util.Map;

import javax.xml.bind.annotation.adapters.XmlAdapter;

import com.google.common.collect.ImmutableMap;

import de.zalando.zmon.domain.Entities;
import de.zalando.zmon.domain.Entity;
import de.zalando.zmon.domain.EntityAttribute;

public class EntityListAdapter extends XmlAdapter<Entities, List<Map<String, String>>> {

    @Override
    public List<Map<String, String>> unmarshal(final Entities v) {

        final List<Map<String, String>> result = new LinkedList<>();
        if (v != null && v.getEntities() != null) {
            for (final Entity entity : v.getEntities()) {
                final ImmutableMap.Builder<String, String> builder = ImmutableMap.builder();

                final List<EntityAttribute> attributes = entity.getAttributes();
                if (attributes != null) {
                    for (final EntityAttribute attribute : attributes) {
                        builder.put(attribute.getKey(), attribute.getValue());
                    }
                }

                result.add(builder.build());
            }
        }

        return result;
    }

    @Override
    public Entities marshal(final List<Map<String, String>> v) {

        final Entities result = new Entities();
        if (v != null) {
            final List<Entity> entities = new LinkedList<>();
            for (final Map<String, String> map : v) {
                final List<EntityAttribute> attributes = new LinkedList<>();

                for (final Map.Entry<String, String> entry : map.entrySet()) {
                    attributes.add(EntityAttribute.from(entry.getKey(), entry.getValue()));
                }

                final Entity entity = new Entity();
                entity.setAttributes(attributes);
                entities.add(entity);
            }

            result.setEntities(entities);
        }

        return result;
    }
}
