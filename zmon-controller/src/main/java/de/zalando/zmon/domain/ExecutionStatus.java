package de.zalando.zmon.domain;

import java.util.Set;

import com.google.common.base.Preconditions;
import com.google.common.collect.ImmutableSet;

/**
 * Created by pribeiro on 17/07/14.
 */
public class ExecutionStatus {

    private final int workersActive;
    private final int workersTotal;
    private final int checkInvocations;
    private final int queueSize;
    private final Set<Worker> workers;
    private final Set<Queue> queues;

    private ExecutionStatus(final Builder builder) {
        this.workersActive = builder.workersActive;
        this.workers = builder.workers.build();
        this.queues = builder.queues.build();
        this.workersTotal = this.workers.size();
        this.checkInvocations = checkInvocations(this.workers);
        this.queueSize = totalQueueSize(this.queues);
    }

    public int getWorkersActive() {
        return workersActive;
    }

    public int getWorkersTotal() {
        return workersTotal;
    }

    public int getCheckInvocations() {
        return checkInvocations;
    }

    public int getQueueSize() {
        return queueSize;
    }

    public Set<Worker> getWorkers() {
        return workers;
    }

    public Set<Queue> getQueues() {
        return queues;
    }

    @Override
    public String toString() {
        final StringBuilder sb = new StringBuilder("ExecutionStatus{");
        sb.append("workersActive=").append(workersActive);
        sb.append(", workersTotal=").append(workersTotal);
        sb.append(", checkInvocations=").append(checkInvocations);
        sb.append(", queueSize=").append(queueSize);
        sb.append(", workers=").append(workers);
        sb.append(", queues=").append(queues);
        sb.append('}');
        return sb.toString();
    }

    public static Builder builder() {
        return new Builder();
    }

    private static int totalQueueSize(final Set<Queue> queues) {
        int totalSize = 0;
        for (final Queue q : queues) {
            totalSize += q.size;
        }

        return totalSize;
    }

    private static int checkInvocations(final Set<Worker> workers) {
        int totalInvocations = 0;
        for (final Worker w : workers) {
            totalInvocations += w.checkInvocations;
        }

        return totalInvocations;
    }

    public static final class Builder {

        // optional
        private int workersActive = 0;
        private final ImmutableSet.Builder<Worker> workers = ImmutableSet.builder();
        private final ImmutableSet.Builder<Queue> queues = ImmutableSet.builder();

        private Builder() { }

        public Builder withWorkersActive(final int workersActive) {
            Preconditions.checkNotNull(workersActive >= 0);
            this.workersActive = workersActive;

            return this;
        }

        public Builder addWorker(final String name, final long lastExecutionTime, final long checkInvocations) {
            Preconditions.checkNotNull(name);
            Preconditions.checkArgument(lastExecutionTime >= 0);
            Preconditions.checkArgument(checkInvocations >= 0);
            workers.add(new Worker(name, lastExecutionTime, checkInvocations));

            return this;
        }

        public Builder addQueue(final String name, final long size) {
            Preconditions.checkNotNull(name);
            Preconditions.checkArgument(size >= 0);
            queues.add(new Queue(name, size));

            return this;
        }

        public ExecutionStatus build() {
            return new ExecutionStatus(this);
        }
    }

    public static final class Queue {

        private final String name;
        private final long size;

        public Queue(final String name, final long size) {
            this.name = Preconditions.checkNotNull(name);
            this.size = size;
        }

        public String getName() {
            return name;
        }

        public long getSize() {
            return size;
        }

        @Override
        public boolean equals(final Object o) {
            if (this == o) {
                return true;
            }

            if (o == null || getClass() != o.getClass()) {
                return false;
            }

            final Queue queue = (Queue) o;

            if (!name.equals(queue.name)) {
                return false;
            }

            return true;
        }

        @Override
        public int hashCode() {
            return name.hashCode();
        }

        @Override
        public String toString() {
            final StringBuilder sb = new StringBuilder("Worker{");
            sb.append("name=").append(name);
            sb.append(", size=").append(size);
            sb.append('}');
            return sb.toString();
        }
    }

    public static final class Worker {

        private final String name;
        private final long lastExecutionTime;
        private final long checkInvocations;

        public Worker(final String name, final long lastExecutionTime, final long checkInvocations) {
            this.name = Preconditions.checkNotNull(name);
            this.lastExecutionTime = lastExecutionTime;
            this.checkInvocations = checkInvocations;
        }

        public String getName() {
            return name;
        }

        public long getLastExecutionTime() {
            return lastExecutionTime;
        }

        public long getCheckInvocations() {
            return checkInvocations;
        }

        @Override
        public boolean equals(final Object o) {
            if (this == o) {
                return true;
            }

            if (o == null || getClass() != o.getClass()) {
                return false;
            }

            final Worker worker = (Worker) o;

            if (!name.equals(worker.name)) {
                return false;
            }

            return true;
        }

        @Override
        public int hashCode() {
            return name.hashCode();
        }

        @Override
        public String toString() {
            final StringBuilder sb = new StringBuilder("Worker{");
            sb.append("name='").append(name).append('\'');
            sb.append(", lastExecutionTime=").append(lastExecutionTime);
            sb.append(", checkInvocations=").append(checkInvocations);
            sb.append('}');
            return sb.toString();
        }
    }
}
