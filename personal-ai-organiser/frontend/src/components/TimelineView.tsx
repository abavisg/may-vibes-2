import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useData } from '../context/DataContext';
import { DragDropContext, Droppable, Draggable } from 'react-beautiful-dnd';
import './Timeline.css';

// Define the shape of a timeline item
interface TimelineItem {
  id: string;
  type: 'event' | 'task';
  summary?: string;
  title?: string;
  start: string | null;
  end: string | null;
  priority?: string | null;
  estimate_minutes?: number | null;
  deadline?: string | null;
  url?: string | null;
}

// TODO: Fetch combined calendar events and scheduled tasks
// TODO: Implement timeline view (e.g., hourly slots)
// TODO: Implement drag and drop for task reordering (optional)

const TimelineView: React.FC = () => {
  const { isAuthenticated } = useAuth();
  const { calendarEvents, notionTasks, isLoading, error } = useData();
  const [timeSlots, setTimeSlots] = useState<string[]>([]);
  const [itemsByTimeSlot, setItemsByTimeSlot] = useState<Record<string, TimelineItem[]>>({});

  // Generate time slots for working hours (9-5)
  useEffect(() => {
    const slots: string[] = [];
    for (let i = 9; i <= 17; i++) {
      const hour = i.toString().padStart(2, '0');
      slots.push(`${hour}:00`);
    }
    setTimeSlots(slots);
  }, []);

  // Process calendar events and tasks
  useEffect(() => {
    if (timeSlots.length === 0) return;

    // Initialize empty slots
    const newItemsBySlot: Record<string, TimelineItem[]> = {};
    timeSlots.forEach(slot => {
      newItemsBySlot[slot] = [];
    });

    // Process calendar events
    calendarEvents.forEach(event => {
      if (event.start) {
        const itemHour = new Date(event.start).getHours();
        const slotHour = itemHour.toString().padStart(2, '0');
        const slotKey = `${slotHour}:00`;
        
        if (newItemsBySlot[slotKey]) {
          newItemsBySlot[slotKey].push({
            ...event,
            type: 'event' as const,
            id: `event-${event.id || Math.random().toString(36).substring(2, 15)}`,
          });
        }
      }
    });

    // Process Notion tasks
    notionTasks.forEach(task => {
      const estimatedMinutes = task.estimate_minutes || 30; // Default to 30 minutes if not specified
      const estimatedHours = estimatedMinutes / 60; // Convert to hours for slot calculation
      
      // Find first available slot
      let placed = false;
      for (let i = 0; i < timeSlots.length; i++) {
        const slotKey = timeSlots[i];
        
        // Check if this slot and next slots are available
        let canPlace = true;
        for (let j = 0; j < estimatedHours; j++) {
          const checkIndex = i + j;
          if (checkIndex >= timeSlots.length || newItemsBySlot[timeSlots[checkIndex]].length > 0) {
            canPlace = false;
            break;
          }
        }
        
        if (canPlace) {
          // Place task in this slot
          const taskWithTime = {
            ...task,
            type: 'task' as const,
            id: `task-${task.id || Math.random().toString(36).substring(2, 15)}`,
            start: new Date(new Date().setHours(parseInt(slotKey.split(':')[0]), 0, 0, 0)).toISOString(),
            end: new Date(new Date().setHours(parseInt(slotKey.split(':')[0]), estimatedMinutes, 0, 0)).toISOString(),
          };
          
          newItemsBySlot[slotKey].push(taskWithTime);
          
          // Mark next slots as occupied if task spans multiple hours
          for (let j = 1; j < estimatedHours; j++) {
            const nextSlotKey = timeSlots[i + j];
            newItemsBySlot[nextSlotKey].push({
              id: `placeholder-${taskWithTime.id}-${j}`,
              type: 'task' as const,
              title: `(Continued) ${task.title}`,
              start: null,
              end: null,
            });
          }
          
          placed = true;
          break;
        }
      }
      
      // If no slot available, place at end of day
      if (!placed && timeSlots.length > 0) {
        const lastSlot = timeSlots[timeSlots.length - 1];
        const taskWithTime = {
          ...task,
          type: 'task' as const,
          id: `task-${task.id || Math.random().toString(36).substring(2, 15)}`,
          start: new Date(new Date().setHours(parseInt(lastSlot.split(':')[0]), 0, 0, 0)).toISOString(),
          end: new Date(new Date().setHours(parseInt(lastSlot.split(':')[0]), estimatedMinutes, 0, 0)).toISOString(),
        };
        
        newItemsBySlot[lastSlot].push(taskWithTime);
      }
    });

    setItemsByTimeSlot(newItemsBySlot);
  }, [calendarEvents, notionTasks, timeSlots]);

  const formatTime = (isoString: string | null): string => {
    if (!isoString) return "Time N/A";
    try {
      return new Date(isoString).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });
    } catch { return "Invalid Date"; }
  };

  const formatTimeRange = (start: string | null, end: string | null): string => {
    if (!start || !end) return "Time N/A";
    try {
      const startTime = new Date(start).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });
      const endTime = new Date(end).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });
      return `${startTime}–${endTime}`;
    } catch { return "Invalid Time Range"; }
  };

  const handleDragEnd = (result: any) => {
    if (!result.destination) return;

    const { source, destination } = result;
    
    // If dropped in the same position, do nothing
    if (
      source.droppableId === destination.droppableId &&
      source.index === destination.index
    ) {
      return;
    }

    // Create a copy of the items by time slot
    const newItemsByTimeSlot = { ...itemsByTimeSlot };
    
    // Get the source and destination arrays
    const sourceItems = [...newItemsByTimeSlot[source.droppableId]];
    const destItems = source.droppableId === destination.droppableId 
      ? sourceItems 
      : [...newItemsByTimeSlot[destination.droppableId]];
    
    // Remove the dragged item from its original position
    const [removed] = sourceItems.splice(source.index, 1);
    
    // Insert the dragged item at its new position
    destItems.splice(destination.index, 0, removed);
    
    // Update the state with the new order
    newItemsByTimeSlot[source.droppableId] = sourceItems;
    newItemsByTimeSlot[destination.droppableId] = destItems;
    
    setItemsByTimeSlot(newItemsByTimeSlot);
  };

  if (isLoading) {
    return <div className="timeline-loading">Loading timeline...</div>;
  }

  if (error) {
    return <div className="timeline-error">{error}</div>;
  }

  // Check if there are any items to display
  const hasItems = Object.values(itemsByTimeSlot).some(slot => slot.length > 0);

  return (
    <div className="timeline-container">
      {!hasItems ? (
        <p className="text-gray-500 dark:text-gray-400 text-center py-4">No items found for today.</p>
      ) : (
        <DragDropContext onDragEnd={handleDragEnd}>
          <div className="timeline">
            {timeSlots.map((timeSlot, index) => {
              const nextTimeSlot = index < timeSlots.length - 1 ? timeSlots[index + 1] : null;
              const currentHour = parseInt(timeSlot.split(':')[0]);
              const nextHour = nextTimeSlot ? parseInt(nextTimeSlot.split(':')[0]) : currentHour + 1;
              
              return (
                <div key={timeSlot} className="time-slot">
                  <div className="time-label">{formatTimeRange(
                    new Date().setHours(currentHour, 0, 0, 0).toString(),
                    new Date().setHours(nextHour, 0, 0, 0).toString()
                  )}</div>
                  <Droppable droppableId={timeSlot}>
                    {(provided) => (
                      <div
                        ref={provided.innerRef}
                        {...provided.droppableProps}
                        className="droppable-area"
                      >
                        {itemsByTimeSlot[timeSlot]?.map((item, index) => (
                          <Draggable key={item.id} draggableId={item.id} index={index}>
                            {(provided, snapshot) => (
                              <div
                                ref={provided.innerRef}
                                {...provided.draggableProps}
                                {...provided.dragHandleProps}
                                className={`timeline-item ${item.type === 'event' ? 'event-item' : 'task-item'} ${snapshot.isDragging ? 'dragging' : ''}`}
                              >
                                <div className="item-content">
                                  <span className="item-type">
                                    {item.type === 'event' ? '(calendar)' : '(task)'}
                                  </span>
                                  <div className="timeline-item-content">
                                    <div className="timeline-item-title">{item.summary || item.title}</div>
                                    <div className="timeline-item-duration">{formatTimeRange(item.start, item.end)}</div>
                                  </div>
                                </div>
                              </div>
                            )}
                          </Draggable>
                        ))}
                        {provided.placeholder}
                      </div>
                    )}
                  </Droppable>
                </div>
              );
            })}
          </div>
        </DragDropContext>
      )}
    </div>
  );
};

export default TimelineView; 