from typing import Any, Dict, List

import pandas as pd
import streamlit as st


def metric_row(metrics: List[Dict[str, Any]]):
    cols = st.columns(len(metrics))
    for col, m in zip(cols, metrics):
        col.metric(m["label"], m["value"])


def render_table(title: str, data: List[Dict[str, Any]], columns: List[str]):
    st.markdown(f"**{title}**")
    if not data:
        st.info("Kayıt yok")
        return
    df = pd.DataFrame(data)
    st.dataframe(df[columns], use_container_width=True, hide_index=True)


def spec_block(spec: Dict[str, Any]):
    with st.container():
        st.markdown("**Ürün Özeti**")
        cols = st.columns(3)
        cols[0].write(f"Genişlik (mm): **{spec.get('width_mm', '-')}**")
        cols[1].write(f"Yükseklik (mm): **{spec.get('height_mm', '-')}**")
        cols[2].write(f"Uzunluk (mm): **{spec.get('length_mm', '-')}**")
        cols2 = st.columns(3)
        cols2[0].write(f"Sac Kalınlığı (mm): **{spec.get('thickness_mm', '-')}**")
        cols2[1].write(f"Yalıtım: **{'Açık' if spec.get('insulation_enabled') else 'Kapalı'}**")
        cols2[2].write(f"Yalıtım Kalınlığı (mm): **{spec.get('insulation_thickness_mm') or 0}**")


def card(title: str, body: str):
    with st.container():
        st.markdown(f"### {title}")
        st.markdown(body)


def success(msg: str):
    st.success(msg)


def error(msg: str):
    st.error(msg)


def warning(msg: str):
    st.warning(msg)


def info(msg: str):
    st.info(msg)


