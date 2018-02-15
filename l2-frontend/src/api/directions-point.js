import {HTTP} from '../http-common'

async function sendDirections(card_pk, diagnos, fin_source, history_num, ofname_pk, researches, comments) {
  try {
    const response = await HTTP.post('directions/generate', {
      card_pk,
      diagnos,
      fin_source,
      history_num,
      ofname_pk,
      researches,
      comments
    })
    if (response.statusText === 'OK') {
      return response.data
    }
  } catch (e) {
  }
  return {ok: false, directions: [], message: ''}
}

async function getHistory(type, patient, date_from, date_to) {
  try {
    const response = await HTTP.post('directions/history', {
      type,
      patient,
      date_from,
      date_to
    })
    if (response.statusText === 'OK') {
      return response.data
    }
  } catch (e) {
  }
  return {directions: []}
}

async function cancelDirection(pk) {
  try {
    const response = await HTTP.post('directions/cancel', {pk})
    if (response.statusText === 'OK') {
      return response.data
    }
  } catch (e) {
  }
  return {cancel: false}
}

async function getResults(pk) {
  try {
    const response = await HTTP.post('directions/results', {pk})
    if (response.statusText === 'OK') {
      return response.data
    }
  } catch (e) {
  }
  return {ok: false}
}

async function getParaclinicForm(pk) {
  try {
    const response = await HTTP.post('directions/paraclinic_form', {pk})
    if (response.statusText === 'OK') {
      return response.data
    }
  } catch (e) {
  }
  return {ok: false, message: ''}
}

async function paraclinicResultSave(data, with_confirm) {
  try {
    const response = await HTTP.post('directions/paraclinic_result', {data, with_confirm})
    if (response.statusText === 'OK') {
      return response.data
    }
  } catch (e) {
  }
  return {ok: false, message: ''}
}

async function paraclinicResultConfirm(iss_pk) {
  try {
    const response = await HTTP.post('directions/paraclinic_result_confirm', {iss_pk})
    if (response.statusText === 'OK') {
      return response.data
    }
  } catch (e) {
  }
  return {ok: false, message: ''}
}

async function paraclinicResultConfirmReset(iss_pk) {
  try {
    const response = await HTTP.post('directions/paraclinic_result_confirm_reset', {iss_pk})
    if (response.statusText === 'OK') {
      return response.data
    }
  } catch (e) {
  }
  return {ok: false, message: ''}
}

async function paraclinicResultUserHistory(date) {
  try {
    const response = await HTTP.post('directions/paraclinic_result_history', {date})
    if (response.statusText === 'OK') {
      return response.data
    }
  } catch (e) {
  }
  return {directions: []}
}


export default {
  sendDirections,
  getHistory,
  cancelDirection,
  getResults,
  getParaclinicForm,
  paraclinicResultSave,
  paraclinicResultConfirm,
  paraclinicResultConfirmReset,
  paraclinicResultUserHistory
}
