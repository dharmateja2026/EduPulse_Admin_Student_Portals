CREATE DATABASE IF NOT EXISTS student_feedback
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE student_feedback;

CREATE TABLE IF NOT EXISTS courses (
  course_id INT AUTO_INCREMENT PRIMARY KEY,
  course_code VARCHAR(12) NOT NULL UNIQUE,
  course_name VARCHAR(180) NOT NULL
);

CREATE TABLE IF NOT EXISTS feedback_questions (
  question_id INT AUTO_INCREMENT PRIMARY KEY,
  question_text VARCHAR(500) NOT NULL,
  question_order TINYINT NOT NULL UNIQUE
);

-- One anonymous submission per course; each of the five answers is a row.
-- No student name, email, or IP address is stored.
CREATE TABLE IF NOT EXISTS feedback (
  feedback_id BIGINT AUTO_INCREMENT PRIMARY KEY,
  submission_token CHAR(36) NOT NULL,
  course_id INT NOT NULL,
  question_id INT NOT NULL,
  rating TINYINT NOT NULL,
  comment_optional VARCHAR(500) NULL,
  submitted_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_feedback_course FOREIGN KEY (course_id) REFERENCES courses(course_id),
  CONSTRAINT fk_feedback_question FOREIGN KEY (question_id) REFERENCES feedback_questions(question_id),
  CONSTRAINT chk_rating CHECK (rating BETWEEN 1 AND 5),
  INDEX idx_feedback_course_time (course_id, submitted_at),
  INDEX idx_feedback_question (question_id),
  INDEX idx_submission_token (submission_token)
);

INSERT IGNORE INTO courses (course_code, course_name) VALUES
('CDCT','Communication Excellence and Soft Skills'),
('PEDH','Python Essentials for Data Handling and Web Integration'),
('IDSA','Industry Data Structures and Algorithms'),
('OS','Operating Systems'),
('DBMS','Database Management Systems');

INSERT IGNORE INTO feedback_questions (question_text, question_order) VALUES
('How clearly are the subject concepts explained?',1),
('How effective are the teaching methods and examples?',2),
('How well does the course content match the syllabus?',3),
('How helpful are the assignments, practicals, and learning materials?',4),
('Overall, how satisfied are you with this course?',5);
