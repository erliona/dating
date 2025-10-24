<template>
  <div class="onboarding-view tg-viewport tg-safe-area">
    <!-- Progress Bar -->
    <div class="progress-container">
      <div class="progress-bar">
        <div 
          class="progress-fill" 
          :style="{ width: `${(currentStep / totalSteps) * 100}%` }"
        ></div>
      </div>
      <span class="progress-text">{{ currentStep }} / {{ totalSteps }}</span>
    </div>

    <!-- Step Content -->
    <div class="step-container">
      <component 
        :is="currentStepComponent" 
        v-model="formData"
        @next="nextStep"
        @prev="prevStep"
        @complete="completeOnboarding"
      />
    </div>

    <!-- Navigation -->
    <div class="navigation-container">
      <button 
        v-if="currentStep > 1"
        class="btn btn-outline"
        @click="prevStep"
      >
        ← Назад
      </button>
      
      <button 
        v-if="currentStep < totalSteps"
        class="btn btn-primary"
        @click="nextStep"
        :disabled="!canProceed"
      >
        Далее →
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import { useTelegram } from '../composables/useTelegram'
import { useApi } from '../composables/useApi'

// Import step components
import StepBasicInfo from '../components/onboarding/StepBasicInfo.vue'
import StepPreferences from '../components/onboarding/StepPreferences.vue'
import StepBio from '../components/onboarding/StepBio.vue'
import StepInterests from '../components/onboarding/StepInterests.vue'
import StepAdditional from '../components/onboarding/StepAdditional.vue'
import StepPhotos from '../components/onboarding/StepPhotos.vue'

const router = useRouter()
const userStore = useUserStore()
const { hapticFeedback } = useTelegram()
const { api } = useApi()

const currentStep = ref(1)
const totalSteps = 6
const loading = ref(false)

// Form data
const formData = ref({
  // Step 1: Basic Info
  name: '',
  birth_date: '',
  gender: '',
  
  // Step 2: Preferences
  orientation: '',
  goal: [],
  
  // Step 3: Bio
  bio: '',
  
  // Step 4: Interests
  interests: [],
  
  // Step 5: Additional
  height_cm: '',
  education: '',
  profession: '',
  languages: [],
  has_children: null,
  wants_children: null,
  smoking: null,
  drinking: null,
  
  // Step 6: Photos
  photos: []
})

// Step components mapping
const stepComponents = {
  1: StepBasicInfo,
  2: StepPreferences,
  3: StepBio,
  4: StepInterests,
  5: StepAdditional,
  6: StepPhotos
}

const currentStepComponent = computed(() => {
  return stepComponents[currentStep.value]
})

const canProceed = computed(() => {
  switch (currentStep.value) {
    case 1: // Basic Info
      return formData.value.name && formData.value.birth_date && formData.value.gender
    case 2: // Preferences
      return formData.value.orientation && formData.value.goal.length > 0
    case 3: // Bio (optional)
      return true
    case 4: // Interests (optional)
      return true
    case 5: // Additional (optional)
      return true
    case 6: // Photos
      return formData.value.photos.length >= 3
    default:
      return false
  }
})

const nextStep = () => {
  if (currentStep.value < totalSteps && canProceed.value) {
    hapticFeedback('impact')
    currentStep.value++
  }
}

const prevStep = () => {
  if (currentStep.value > 1) {
    hapticFeedback('impact')
    currentStep.value--
  }
}

const completeOnboarding = async () => {
  loading.value = true
  
  try {
    // Prepare profile data with user_id
    const profileData = {
      ...formData.value,
      user_id: userStore.user.id  // Use internal DB user ID
    }
    
    // Create profile via API (POST, not PUT)
    const response = await api.post('/profiles', profileData)
    userStore.profile = response.data
    
    hapticFeedback('notification')
    
    // Redirect to discovery
    router.push('/discovery')
    
  } catch (error) {
    // Handle error
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  // Initialize form with existing profile data if available
  if (userStore.profile) {
    Object.assign(formData.value, userStore.profile)
  }
})
</script>

<style scoped>
.onboarding-view {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: var(--bg-primary);
}

.progress-container {
  display: flex;
  align-items: center;
  padding: var(--spacing-sm);
  background-color: var(--bg-secondary);
  border-bottom: 1px solid var(--border-color);
}

.progress-bar {
  flex: 1;
  height: 3px;
  background-color: var(--bg-tertiary);
  border-radius: 2px;
  overflow: hidden;
  margin-right: var(--spacing-sm);
}

.progress-fill {
  height: 100%;
  background-color: var(--primary-color);
  transition: width var(--transition-normal);
}

.progress-text {
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
  color: var(--text-secondary);
  min-width: 30px;
}

.step-container {
  flex: 1;
  overflow-y: auto;
  padding: var(--spacing-md);
}

.navigation-container {
  display: flex;
  justify-content: space-between;
  padding: var(--spacing-md);
  background-color: var(--bg-secondary);
  border-top: 1px solid var(--border-color);
}

.navigation-container .btn {
  min-width: 80px;
}

.navigation-container .btn:only-child {
  margin-left: auto;
}
</style>
