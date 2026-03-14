<template>
  <div class="chart-container">
    <canvas ref="chartCanvas"></canvas>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { Chart, registerables } from 'chart.js'

Chart.register(...registerables)

const props = defineProps({
  data: {
    type: Object,
    required: true
  }
})

const chartCanvas = ref(null)
let chartInstance = null

onMounted(() => {
  renderChart()
})

watch(() => props.data, () => {
  if (chartInstance) {
    chartInstance.destroy()
  }
  renderChart()
}, { deep: true })

const renderChart = () => {
  if (!chartCanvas.value) return

  const ctx = chartCanvas.value.getContext('2d')
  
  chartInstance = new Chart(ctx, {
    type: 'bar',
    data: props.data,
    options: {
      responsive: true,
      maintainAspectRatio: true,
      plugins: {
        legend: {
          display: false
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          ticks: {
            precision: 0
          }
        }
      }
    }
  })
}
</script>

<style scoped>
.chart-container {
  position: relative;
  height: 300px;
}
</style>
