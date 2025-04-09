import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useData } from '../context/DataContext';
import './Timeline.css';
import { format, differenceInMinutes, addMinutes, set } from 'date-fns';

// Define the shape of a timeline item
interface TimelineItem {
  id: string;
  title: string;
  type: 'task' | 'event';
  start: string;
  end: string;
  duration: number; // duration in minutes
}

// Round up to the next 15-minute interval
const roundToNext15Minutes = (date: Date): Date => {
  const minutes = date.getMinutes();
  const remainder = minutes % 15;
  if (remainder === 0) return date;
  const minutesToAdd = 15 - remainder;
  return addMinutes(date, minutesToAdd);
};

// TODO: Fetch combined calendar events and scheduled tasks
// TODO: Implement timeline view (e.g., hourly slots)
// TODO: Implement drag and drop for task reordering (optional)

const formatTimeAndDuration = (start: string, end: string, duration: number): string => {
  try {
    const startTime = new Date(start);
    const endTime = new Date(end);
    const hours = Math.floor(duration / 60);
    const minutes = duration % 60;
    const timeRange = `${format(startTime, 'HH:mm')} - ${format(endTime, 'HH:mm')}`;
    
    if (hours > 0) {
      return `${timeRange} (${hours}h${minutes > 0 ? ` ${minutes}m` : ''})`;
    }
    return `${timeRange} (${minutes}m)`;
  } catch (error) {
    return 'Invalid time';
  }
};

const TimelineView: React.FC = () => {
  const { isAuthenticated } = useAuth();
  const { calendarEvents, notionTasks, isLoading, error } = useData();
  const [items, setItems] = useState<TimelineItem[]>([]);

  useEffect(() => {
    const processedItems: TimelineItem[] = [];
    const today = new Date();
    
    // Set up working hours boundaries
    const workStart = set(today, { hours: 9, minutes: 0, seconds: 0, milliseconds: 0 });
    const workEnd = set(today, { hours: 17, minutes: 0, seconds: 0, milliseconds: 0 });

    // First, process calendar events within working hours
    calendarEvents.forEach(event => {
      if (event.start && event.end) {
        const startTime = new Date(event.start);
        const endTime = new Date(event.end);
        
        // Only include events that start before 5 PM and after 9 AM
        if (startTime >= workStart && startTime < workEnd) {
          const duration = differenceInMinutes(endTime, startTime);
          processedItems.push({
            id: `event-${event.id || Math.random().toString(36).substring(2, 15)}`,
            title: event.title || event.summary || 'Untitled Event',
            type: 'event',
            start: startTime.toISOString(),
            end: endTime.toISOString(),
            duration
          });
        }
      }
    });

    // Sort events chronologically
    processedItems.sort((a, b) => new Date(a.start).getTime() - new Date(b.start).getTime());

    // Find available time slots
    const findNextAvailableSlot = (durationMinutes: number): Date | null => {
      let currentTime = new Date(workStart);

      while (currentTime < workEnd) {
        // Round up to the next 15-minute interval
        currentTime = roundToNext15Minutes(currentTime);
        const slotEnd = addMinutes(currentTime, durationMinutes);
        
        // Check if we're still within working hours
        if (slotEnd > workEnd) {
          return null;
        }

        // Check if this slot overlaps with any existing items
        const hasOverlap = processedItems.some(item => {
          const itemStart = new Date(item.start);
          const itemEnd = new Date(item.end);
          return (currentTime < itemEnd && slotEnd > itemStart);
        });

        if (!hasOverlap) {
          return currentTime;
        }

        // Move to the end of the current blocking item
        const blockingItem = processedItems.find(item => {
          const itemStart = new Date(item.start);
          const itemEnd = new Date(item.end);
          return (currentTime < itemEnd && slotEnd > itemStart);
        });

        if (blockingItem) {
          currentTime = new Date(blockingItem.end);
        } else {
          currentTime = addMinutes(currentTime, 15);
        }
      }

      return null;
    };

    // Process Notion tasks
    notionTasks.forEach(task => {
      // Get duration in minutes directly from Notion, default to 30 minutes if not set
      const durationMinutes = task.duration || 30;
      const startTime = findNextAvailableSlot(durationMinutes);

      if (startTime) {
        const endTime = addMinutes(startTime, durationMinutes);
        processedItems.push({
          id: `task-${task.id || Math.random().toString(36).substring(2, 15)}`,
          title: task.title || 'Untitled Task',
          type: 'task',
          start: startTime.toISOString(),
          end: endTime.toISOString(),
          duration: durationMinutes
        });
      }
    });

    // Final sort of all items
    processedItems.sort((a, b) => new Date(a.start).getTime() - new Date(b.start).getTime());
    setItems(processedItems);
  }, [calendarEvents, notionTasks]);

  if (isLoading) {
    return <div className="timeline-loading">Loading timeline...</div>;
  }

  if (error) {
    return <div className="timeline-error">{error}</div>;
  }

  return (
    <div className="timeline-container">
      <div className="timeline-list">
        {items.map(item => (
          <div
            key={item.id}
            className={`timeline-item ${item.type}`}
          >
            <div className="item-title">{item.title}</div>
            <div className="item-time">
              {formatTimeAndDuration(item.start, item.end, item.duration)}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default TimelineView; 