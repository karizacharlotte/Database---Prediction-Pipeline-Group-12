-- Insert test student data matching actual schema
-- Your schema: students(student_id uuid, age, sex, address, famsize, pstatus, created_at)

-- Insert a student
INSERT INTO students (age, sex, address, famsize, pstatus)
VALUES (18, 'F', 'U', 'GT3', 'T')
RETURNING student_id;

-- Note: Copy the returned student_id and use it in the commands below
-- Or run the script below which uses a variable

-- Complete script with variable:
DO $$
DECLARE
    v_student_id uuid;
BEGIN
    -- Insert student
    INSERT INTO students (age, sex, address, famsize, pstatus)
    VALUES (18, 'F', 'U', 'GT3', 'T')
    RETURNING student_id INTO v_student_id;
    
    RAISE NOTICE 'Inserted student_id: %', v_student_id;
    
    -- Insert family background
    INSERT INTO family_background (student_id, medu, fedu, mjob, fjob, guardian, fanrel)
    VALUES (v_student_id, 4, 4, 'teacher', 'services', 'mother', 4);
    
    -- Insert academic record (math subject)
    INSERT INTO academic_records (student_id, subject, absences, g1, g2, g3, romantic, freetime, goodt)
    VALUES (v_student_id, 'mat', 4, 15, 16, 17, false, 3, 2);
    
    -- Insert school info
    INSERT INTO school_info (student_id, school, reason, traveltime, studytime, failures, schoolsup, famsup, paid)
    VALUES (v_student_id, 'GP', 'course', 2, 2, 0, true, true, false);
    
    RAISE NOTICE 'All records inserted successfully for student_id: %', v_student_id;
END $$;

-- Query to verify the inserted data
SELECT s.student_id, s.age, s.sex, s.address, s.famsize, s.pstatus,
       fb.medu, fb.fedu, fb.mjob, fb.fjob,
       ar.subject, ar.g1, ar.g2, ar.g3, ar.absences,
       si.school, si.reason, si.studytime
FROM students s
LEFT JOIN family_background fb ON s.student_id = fb.student_id
LEFT JOIN academic_records ar ON s.student_id = ar.student_id
LEFT JOIN school_info si ON s.student_id = si.student_id
ORDER BY s.created_at DESC
LIMIT 1;
