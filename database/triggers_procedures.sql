-- Stored Procedures and Triggers for Student Performance Database

-- ============================================
-- STORED PROCEDURE: Insert Complete Student Record
-- ============================================
-- This procedure inserts a student and related records atomically
CREATE OR REPLACE FUNCTION insert_complete_student(
    p_name VARCHAR(100),
    p_age INTEGER,
    p_sex VARCHAR(1),
    p_address VARCHAR(1),
    p_famsize VARCHAR(3),
    p_pstatus VARCHAR(1),
    p_school VARCHAR(5),
    -- Family background
    p_medu INTEGER,
    p_fedu INTEGER,
    p_mjob VARCHAR(20),
    p_fjob VARCHAR(20),
    p_reason VARCHAR(20),
    p_guardian VARCHAR(10),
    p_traveltime INTEGER,
    p_famrel INTEGER,
    -- Academic records
    p_studytime INTEGER,
    p_failures INTEGER,
    p_schoolsup BOOLEAN,
    p_famsup BOOLEAN,
    p_paid BOOLEAN,
    p_activities BOOLEAN,
    p_nursery BOOLEAN,
    p_higher BOOLEAN,
    p_internet BOOLEAN,
    p_romantic BOOLEAN,
    p_freetime INTEGER,
    p_goout INTEGER,
    p_dalc INTEGER,
    p_walc INTEGER,
    p_health INTEGER,
    p_absences INTEGER,
    p_g1 INTEGER,
    p_g2 INTEGER,
    p_g3 INTEGER
) RETURNS INTEGER AS $$
DECLARE
    v_student_id INTEGER;
    v_at_risk BOOLEAN;
BEGIN
    -- Calculate at_risk status
    v_at_risk := (p_g3 < 10);
    
    -- Insert into students table
    INSERT INTO students (name, age, sex, address, famsize, pstatus, school)
    VALUES (p_name, p_age, p_sex, p_address, p_famsize, p_pstatus, p_school)
    RETURNING student_id INTO v_student_id;
    
    -- Insert into family_background
    INSERT INTO family_background (
        student_id, medu, fedu, mjob, fjob, reason, guardian, traveltime, famrel
    ) VALUES (
        v_student_id, p_medu, p_fedu, p_mjob, p_fjob, p_reason, p_guardian, p_traveltime, p_famrel
    );
    
    -- Insert into academic_records
    INSERT INTO academic_records (
        student_id, studytime, failures, schoolsup, famsup, paid, activities,
        nursery, higher, internet, romantic, freetime, goout, dalc, walc,
        health, absences, g1, g2, g3, at_risk
    ) VALUES (
        v_student_id, p_studytime, p_failures, p_schoolsup, p_famsup, p_paid,
        p_activities, p_nursery, p_higher, p_internet, p_romantic, p_freetime,
        p_goout, p_dalc, p_walc, p_health, p_absences, p_g1, p_g2, p_g3, v_at_risk
    );
    
    -- Insert into school_info
    INSERT INTO school_info (
        student_id, school_name, school_support, family_support, paid_classes,
        activities, nursery, higher_ed_aspiration, internet_access, romantic_relationship
    ) VALUES (
        v_student_id, p_school, p_schoolsup, p_famsup, p_paid, p_activities,
        p_nursery, p_higher, p_internet, p_romantic
    );
    
    RETURN v_student_id;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- STORED PROCEDURE: Calculate At-Risk Students
-- ============================================
-- Updates at_risk flag for all students based on G3 < 10
CREATE OR REPLACE FUNCTION update_at_risk_status()
RETURNS TABLE(student_id INTEGER, at_risk BOOLEAN) AS $$
BEGIN
    UPDATE academic_records
    SET at_risk = (g3 < 10)
    WHERE at_risk != (g3 < 10) OR at_risk IS NULL;
    
    RETURN QUERY
    SELECT ar.student_id, ar.at_risk
    FROM academic_records ar
    WHERE ar.at_risk = TRUE;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- TRIGGER: Audit Log for Student Changes
-- ============================================
-- Automatically logs INSERT, UPDATE, DELETE operations on students table
CREATE OR REPLACE FUNCTION audit_student_changes()
RETURNS TRIGGER AS $$
BEGIN
    IF (TG_OP = 'DELETE') THEN
        INSERT INTO student_audit_log (student_id, action, old_data, changed_by)
        VALUES (OLD.student_id, 'DELETE', row_to_json(OLD), current_user);
        RETURN OLD;
    ELSIF (TG_OP = 'UPDATE') THEN
        INSERT INTO student_audit_log (student_id, action, old_data, new_data, changed_by)
        VALUES (NEW.student_id, 'UPDATE', row_to_json(OLD), row_to_json(NEW), current_user);
        RETURN NEW;
    ELSIF (TG_OP = 'INSERT') THEN
        INSERT INTO student_audit_log (student_id, action, new_data, changed_by)
        VALUES (NEW.student_id, 'INSERT', row_to_json(NEW), current_user);
        RETURN NEW;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Create trigger on students table
DROP TRIGGER IF EXISTS trg_audit_students ON students;
CREATE TRIGGER trg_audit_students
AFTER INSERT OR UPDATE OR DELETE ON students
FOR EACH ROW EXECUTE FUNCTION audit_student_changes();

-- ============================================
-- TRIGGER: Auto-update at_risk on Grade Change
-- ============================================
-- Automatically updates at_risk flag when G3 is updated
CREATE OR REPLACE FUNCTION auto_update_at_risk()
RETURNS TRIGGER AS $$
BEGIN
    NEW.at_risk := (NEW.g3 < 10);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_auto_at_risk ON academic_records;
CREATE TRIGGER trg_auto_at_risk
BEFORE INSERT OR UPDATE OF g3 ON academic_records
FOR EACH ROW EXECUTE FUNCTION auto_update_at_risk();

-- ============================================
-- TRIGGER: Update timestamp on student modification
-- ============================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_update_students_timestamp ON students;
CREATE TRIGGER trg_update_students_timestamp
BEFORE UPDATE ON students
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
