import { DragDropContext, Draggable, Droppable } from "@hello-pangea/dnd";
import { Badge } from "react-bootstrap";
import { Link } from "react-router";
import { statusVariant } from "../components/common";
import { computeMoveToIndex } from "./logic";

const PRIORITY = { low: "secondary", medium: "info", high: "warning", urgent: "danger" };

function Card({ issue, index, linkBase, disabled }) {
  return (
    <Draggable draggableId={issue.id} index={index} isDragDisabled={disabled}>
      {(provided, snapshot) => (
        <div ref={provided.innerRef} {...provided.draggableProps} {...provided.dragHandleProps}
          className={`tt-card${snapshot.isDragging ? " dragging" : ""}`} data-testid={`card-${issue.key}`}
          aria-label={`${issue.key} ${issue.title}. Press space to pick up, arrow keys to move, space to drop.`}>
          <div className="d-flex justify-content-between align-items-start gap-2">
            <Link to={`${linkBase}/issues/${issue.id}`} className="fw-semibold">{issue.key}</Link>
            <Badge bg={PRIORITY[issue.priority]} text={issue.priority === "high" ? "dark" : undefined}>{issue.priority}</Badge>
          </div>
          <div>{issue.title}</div>
          {issue.labels && issue.labels.length > 0 && (
            <div className="d-flex flex-wrap gap-1 my-1">
              {issue.labels.map((lbl) => (
                <Badge key={lbl} bg="light" text="dark" className="border fw-normal" style={{ fontSize: "0.7rem" }}>
                  {lbl}
                </Badge>
              ))}
            </div>
          )}
          <div className="d-flex justify-content-between align-items-center mt-1 small text-muted">
            {issue.assignee_email ? <span>{issue.assignee_email}</span> : <span className="fst-italic">Unassigned</span>}
            {issue.due_date && <span>📅 {issue.due_date}</span>}
          </div>
        </div>
      )}
    </Draggable>
  );
}

function Column({ column, linkBase, disabled }) {
  return (
    <Droppable droppableId={column.id}>
      {(provided, snapshot) => (
        <section className={`tt-column${snapshot.isDraggingOver ? " over" : ""}`} aria-label={`${column.name} column`}
          data-testid={`column-${column.name}`}>
          <h2 className="h6 d-flex justify-content-between">
            <span>{column.name}</span>
            <Badge bg={statusVariant[column.category]} text={column.category === "in_progress" ? "dark" : undefined}>{column.issues.length}</Badge>
          </h2>
          <div ref={provided.innerRef} {...provided.droppableProps} className="tt-drop-empty">
            {column.issues.map((i, index) => <Card key={i.id} issue={i} index={index} linkBase={linkBase} disabled={disabled} />)}
            {provided.placeholder}
          </div>
        </section>
      )}
    </Droppable>
  );
}

/**
 * Controlled board. `onMove(move, previousColumns)` persists the change; the board shows the move
 * optimistically and the parent reverts (via setColumns) when the API rejects it.
 * Pointer, touch and keyboard (space / arrow keys) dragging are provided by @hello-pangea/dnd.
 */
export default function KanbanBoard({ columns, setColumns, onMove, linkBase, readOnly = false }) {
  const handleEnd = ({ draggableId, destination }) => {
    if (!destination || readOnly) return;
    const move = computeMoveToIndex(columns, draggableId, destination.droppableId, destination.index);
    if (!move) return;
    const previous = columns;
    setColumns(move.newColumns); // optimistic
    onMove({ issueId: draggableId, ...move }, previous);
  };

  return (
    <DragDropContext onDragEnd={handleEnd}>
      <div className="tt-kanban">
        {columns.map((c) => <Column key={c.id} column={c} linkBase={linkBase} disabled={readOnly} />)}
      </div>
    </DragDropContext>
  );
}
