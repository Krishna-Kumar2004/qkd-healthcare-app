# ============================================================
# 🔐 FIXED QKD HEALTHCARE STREAMLIT APP
# ============================================================

import streamlit as st
import numpy as np
import pandas as pd
import random
import datetime

from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(page_title="QKD Healthcare", layout="wide")

# ============================================================
# USERS
# ============================================================
USERS = {
    "doctor1": {"password": "doc123", "role": "Doctor", "name": "Dr. Ramesh"},
    "patient1": {"password": "pat123", "role": "Patient", "name": "Alice", "id": "P001"},
}

# ============================================================
# SESSION INIT
# ============================================================
def init():
    defaults = {
        "logged": False,
        "user": "",
        "role": "",
        "name": "",
        "pid": "",
        "key": [],
        "qber": 0,
        "status": "",
        "records": []
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init()

# ============================================================
# BB84 (FIXED)
# ============================================================
def run_qkd(n=32):
    sim = AerSimulator()

    alice_bits = [random.randint(0, 1) for _ in range(n)]
    alice_bases = [random.randint(0, 1) for _ in range(n)]
    bob_bases = [random.randint(0, 1) for _ in range(n)]

    bob_bits = []

    for i in range(n):
        qc = QuantumCircuit(1, 1)

        if alice_bits[i] == 1:
            qc.x(0)
        if alice_bases[i] == 1:
            qc.h(0)

        if bob_bases[i] == 1:
            qc.h(0)

        qc.measure(0, 0)

        result = sim.run(qc, shots=1).result()
        counts = result.get_counts()

        bit = int(list(counts.keys())[0])
        bob_bits.append(bit)

    key = []
    errors = 0
    total = 0

    for i in range(n):
        if alice_bases[i] == bob_bases[i]:
            total += 1
            key.append(alice_bits[i])
            if alice_bits[i] != bob_bits[i]:
                errors += 1

    qber = errors / total if total > 0 else 1
    status = "SECURE" if qber < 0.1 else "INSECURE"

    return key, qber, status

# ============================================================
# ENCRYPTION (SAFE)
# ============================================================
def encrypt(text, key):
    if not key:
        return text

    key_str = ''.join(map(str, key))
    return ''.join(chr(ord(c) ^ ord(key_str[i % len(key_str)])) for i, c in enumerate(text))

def decrypt(text, key):
    return encrypt(text, key)

# ============================================================
# LOGIN
# ============================================================
def login():
    st.title("🔐 QKD Healthcare Login")

    u = st.text_input("Username")
    p = st.text_input("Password", type="password")

    if st.button("Login"):
        if u in USERS and USERS[u]["password"] == p:
            key, qber, status = run_qkd()

            st.session_state.logged = True
            st.session_state.user = u
            st.session_state.role = USERS[u]["role"]
            st.session_state.name = USERS[u]["name"]
            st.session_state.pid = USERS[u].get("id", "")
            st.session_state.key = key
            st.session_state.qber = qber
            st.session_state.status = status

            st.rerun()
        else:
            st.error("Invalid login")

# ============================================================
# DOCTOR DASHBOARD
# ============================================================
def doctor():
    st.title("🩺 Doctor Dashboard")

    if st.session_state.status != "SECURE":
        st.error("QKD NOT SECURE")
        return

    pid = st.text_input("Patient ID")
    name = st.text_input("Name")
    diagnosis = st.text_input("Diagnosis")

    if st.button("Store"):
        data = f"{pid},{name},{diagnosis}"
        enc = encrypt(data, st.session_state.key)

        st.session_state.records.append(enc)
        st.success("Stored securely")

    st.subheader("Records")
    for r in st.session_state.records:
        dec = decrypt(r, st.session_state.key)
        st.write(dec)

# ============================================================
# PATIENT DASHBOARD
# ============================================================
def patient():
    st.title("🧑 Patient Dashboard")

    pid = st.session_state.pid

    for r in st.session_state.records:
        dec = decrypt(r, st.session_state.key)

        if dec.startswith(pid):
            st.write(dec)

# ============================================================
# MAIN
# ============================================================
if not st.session_state.logged:
    login()
else:
    if st.session_state.role == "Doctor":
        doctor()
    else:
        patient()
