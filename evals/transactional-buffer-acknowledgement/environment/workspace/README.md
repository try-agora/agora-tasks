# Durable buffer
Synthetic SQLite-backed output queue. Acknowledgement releases rows for page reuse;
shrinking the database file is not part of this task. append returns a stable integer ID.
