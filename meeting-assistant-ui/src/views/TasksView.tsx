import React, { useState } from 'react';
import { mockTasks } from '../data';
import { cn } from '../lib/utils';
import { 
  Filter, 
  Calendar as CalendarIcon, 
  Bell,
  Check,
  Trash2,
  X,
  ChevronLeft,
  ChevronRight
} from 'lucide-react';

export function TasksView() {
  const [selectedDate, setSelectedDate] = useState<string>('2026-09-16');
  const [selectedProject, setSelectedProject] = useState<string>('All');
  const [isProjectDropdownOpen, setIsProjectDropdownOpen] = useState(false);
  
  const [selectedYear, setSelectedYear] = useState<number>(2026);
  const [selectedMonth, setSelectedMonth] = useState<number>(8); // 8 is September
  const [isYearDropdownOpen, setIsYearDropdownOpen] = useState(false);
  const [completedTaskIds, setCompletedTaskIds] = useState<Set<string>>(new Set());
  
  const projects = ['All', ...Array.from(new Set(mockTasks.map(t => t.project)))];
  const years = Array.from({ length: 11 }, (_, i) => 2026 - 5 + i);
  const months = [
    'January', 'February', 'March', 'April', 'May', 'June', 
    'July', 'August', 'September', 'October', 'November', 'December'
  ];

  const daysInMonth = new Date(selectedYear, selectedMonth + 1, 0).getDate();
  const startDayOfWeek = new Date(selectedYear, selectedMonth, 1).getDay(); 
  
  const calendarGrid = Array.from({ length: 42 }, (_, i) => {
    const day = i - startDayOfWeek + 1;
    return (day > 0 && day <= daysInMonth) ? day : null;
  });

  const getFullDateString = (year: number, month: number, day: number) => {
    return `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
  };

  const tasksForSelectedProject = mockTasks.filter(t => 
    selectedProject === 'All' || t.project === selectedProject
  );

  const hasTaskOnDate = (dateStr: string) => {
    return tasksForSelectedProject.some(t => t.dueDate === dateStr && !completedTaskIds.has(t.id));
  };

  const filteredTasks = tasksForSelectedProject.filter(t => t.dueDate === selectedDate);
  const pendingTasks = filteredTasks.filter(t => !completedTaskIds.has(t.id));
  const completedTasksList = filteredTasks.filter(t => completedTaskIds.has(t.id));

  const handlePrevMonth = () => {
    setSelectedMonth(prev => prev === 0 ? 11 : prev - 1);
  };

  const handleNextMonth = () => {
    setSelectedMonth(prev => prev === 11 ? 0 : prev + 1);
  };

  return (
    <div className="flex flex-col h-full bg-white relative">
      {/* Header */}
      <div className="flex justify-between items-center px-4 pt-12 pb-4 shrink-0 bg-white">
        <div className="relative">
          <button 
            onClick={() => setIsYearDropdownOpen(!isYearDropdownOpen)}
            className="flex items-center space-x-1 text-red-500 hover:opacity-70 transition-opacity"
          >
            <ChevronLeft className="w-6 h-6 -ml-1" />
            <h1 className="text-xl font-semibold tracking-tight">{selectedYear}</h1>
          </button>
          {isYearDropdownOpen && (
            <>
              <div 
                className="fixed inset-0 z-40" 
                onClick={() => setIsYearDropdownOpen(false)}
              />
              <div className="absolute top-full left-0 mt-2 w-32 bg-white rounded-xl shadow-lg border border-gray-100 z-50 overflow-hidden animate-in fade-in zoom-in-95 max-h-60 overflow-y-auto">
                {years.map(year => (
                  <button
                    key={year}
                    onClick={() => { setSelectedYear(year); setIsYearDropdownOpen(false); }}
                    className="w-full flex items-center justify-between px-4 py-3 text-sm hover:bg-gray-50 text-gray-700 border-b border-gray-50 last:border-0 transition-colors"
                  >
                    <span className={cn(selectedYear === year && "font-semibold text-red-500")}>
                      {year}
                    </span>
                    {selectedYear === year && <Check className="w-4 h-4 text-red-500" />}
                  </button>
                ))}
              </div>
            </>
          )}
        </div>
        
        <div className="flex items-center space-x-4 relative">
          <button className="text-red-500 hover:opacity-70 transition-opacity">
            <Bell className="w-5 h-5" />
          </button>
          <div className="relative">
            <button 
              onClick={() => setIsProjectDropdownOpen(!isProjectDropdownOpen)}
              className="text-red-500 hover:opacity-70 transition-opacity flex items-center"
            >
              <Filter className="w-5 h-5" />
            </button>
            {isProjectDropdownOpen && (
              <>
                <div 
                  className="fixed inset-0 z-40" 
                  onClick={() => setIsProjectDropdownOpen(false)}
                />
                <div className="absolute top-full right-0 mt-2 w-48 bg-white rounded-xl shadow-lg border border-gray-100 z-50 overflow-hidden animate-in fade-in zoom-in-95">
                  {projects.map(proj => (
                    <button
                      key={proj}
                      onClick={() => { setSelectedProject(proj); setIsProjectDropdownOpen(false); }}
                      className="w-full flex items-center justify-between px-4 py-3 text-sm hover:bg-gray-50 text-gray-700 border-b border-gray-50 last:border-0 transition-colors"
                    >
                      <span className={cn(selectedProject === proj && "font-semibold text-red-500")}>
                        {proj}
                      </span>
                      {selectedProject === proj && <Check className="w-4 h-4 text-red-500" />}
                    </button>
                  ))}
                </div>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Calendar Widget */}
      <div className="px-4 pb-4 border-b border-gray-100 shrink-0">
        <div className="flex items-center justify-between mb-4">
          <button onClick={handlePrevMonth} className="p-1 -ml-1 text-red-500 hover:opacity-70 transition-opacity rounded-full">
            <ChevronLeft className="w-6 h-6" />
          </button>
          <h2 className="text-2xl font-bold text-gray-900 tracking-tight">
            {months[selectedMonth]}
          </h2>
          <button onClick={handleNextMonth} className="p-1 -mr-1 text-red-500 hover:opacity-70 transition-opacity rounded-full">
            <ChevronRight className="w-6 h-6" />
          </button>
        </div>
        
        {/* Days of week */}
        <div className="grid grid-cols-7 mb-2">
          {['SUN', 'MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT'].map((day, i) => (
            <div key={day} className={cn(
              "text-[10px] font-bold text-center tracking-wider",
              i === 0 || i === 6 ? "text-gray-400" : "text-blue-500"
            )}>
              {day}
            </div>
          ))}
        </div>

        {/* Calendar Grid */}
        <div className="grid grid-cols-7 gap-y-2">
          {calendarGrid.map((day, i) => {
            if (day === null) {
              return <div key={i} className="h-10"></div>;
            }
            
            const dateStr = getFullDateString(selectedYear, selectedMonth, day);
            const isSelected = dateStr === selectedDate;
            const hasTask = hasTaskOnDate(dateStr);
            const isToday = dateStr === '2026-09-16';

            return (
              <button 
                key={i}
                onClick={() => setSelectedDate(dateStr)}
                className="flex flex-col items-center justify-center h-10 relative group"
              >
                <div className={cn(
                  "w-8 h-8 flex items-center justify-center rounded-full text-sm font-medium transition-colors",
                  isSelected ? "bg-blue-500 text-white" : "text-gray-700 group-hover:bg-gray-100",
                  !isSelected && isToday && "text-blue-600 font-bold"
                )}>
                  {day}
                </div>
                {/* Dot indicator for tasks */}
                <div className="h-1.5 flex items-center justify-center absolute bottom-0">
                  {hasTask && (
                    <div className={cn(
                      "w-1 h-1 rounded-full",
                      isSelected ? "bg-white" : "bg-green-500"
                    )}></div>
                  )}
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Selected Day Info */}
      <div className="px-4 py-3 border-b border-gray-100 flex items-center justify-between shrink-0 bg-gray-50/50">
        <h3 className="text-sm font-bold text-blue-500 uppercase tracking-wide">
          {selectedDate === '2026-09-16' ? 'Today ' : ''}
          <span className="text-blue-400 font-medium">{selectedDate}</span>
        </h3>
      </div>

      {/* Task List */}
      <div className="flex-1 overflow-y-auto p-4 pb-24 space-y-4">
        {pendingTasks.length === 0 && completedTasksList.length === 0 ? (
          <div className="text-center text-sm text-gray-400 mt-10">
            No tasks due on this date.
          </div>
        ) : (
          <div className="space-y-3">
            {pendingTasks.map(task => (
              <div key={task.id} className="flex items-center justify-between p-3 bg-white rounded-2xl border border-gray-100 shadow-sm">
                <div className="flex items-center space-x-3 flex-1 min-w-0 pr-4">
                  <div className={cn("w-10 h-10 rounded-full flex items-center justify-center text-white text-sm font-semibold shrink-0", task.assignee.color)}>
                    {task.assignee.initials}
                  </div>
                  <div className="truncate">
                    <p className="text-sm font-bold text-gray-900 truncate">{task.title}</p>
                    <p className="text-xs text-gray-500 flex items-center space-x-1.5">
                      <span className="font-medium">{task.assignee.name}</span>
                      <span className="w-1 h-1 rounded-full bg-gray-300"></span>
                      <span className="text-gray-400">{task.project}</span>
                    </p>
                  </div>
                </div>
                <div className="flex items-center space-x-2 shrink-0">
                  <button 
                    onClick={() => {
                      setCompletedTaskIds(prev => new Set(prev).add(task.id));
                    }}
                    className="w-8 h-8 flex items-center justify-center rounded-full bg-gray-100 text-gray-400 hover:bg-green-100 hover:text-green-600 transition-colors"
                  >
                    <Check className="w-4 h-4" />
                  </button>
                  <button className="w-8 h-8 flex items-center justify-center rounded-full bg-gray-100 text-gray-400 hover:bg-red-100 hover:text-red-600 transition-colors">
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {completedTasksList.length > 0 && (
          <div className="pt-4 border-t border-gray-100">
            <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3 px-1">Completed</h3>
            <div className="space-y-3">
              {completedTasksList.map(task => (
                <div key={task.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-2xl border border-gray-100 shadow-sm opacity-60">
                  <div className="flex items-center space-x-3 flex-1 min-w-0 pr-4">
                    <div className={cn("w-10 h-10 rounded-full flex items-center justify-center text-white text-sm font-semibold shrink-0 grayscale", task.assignee.color)}>
                      {task.assignee.initials}
                    </div>
                    <div className="truncate">
                      <p className="text-sm font-bold text-gray-500 line-through truncate">{task.title}</p>
                      <p className="text-xs text-gray-400 flex items-center space-x-1.5">
                        <span className="font-medium">{task.assignee.name}</span>
                        <span className="w-1 h-1 rounded-full bg-gray-200"></span>
                        <span>{task.project}</span>
                      </p>
                    </div>
                  </div>
                  <button 
                    onClick={() => {
                      setCompletedTaskIds(prev => {
                        const next = new Set(prev);
                        next.delete(task.id);
                        return next;
                      });
                    }}
                    className="text-xs font-semibold text-blue-600 hover:text-blue-800 transition-colors px-3 py-1.5"
                  >
                    Undo
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
