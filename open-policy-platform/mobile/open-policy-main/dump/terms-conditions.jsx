import { View, Text, TouchableOpacity, ScrollView } from 'react-native'
import React from 'react'
import { SafeAreaView } from 'react-native-safe-area-context'
import terms from '../constants/terms'
import { Ionicons } from '@expo/vector-icons'
import { router } from 'expo-router'

const TermsAndConditions = () => {
  const sections = terms.termsOfServiceSections;
  return (
    <SafeAreaView className="flex-1 bg-white h-full">
            <View className="mb-10 mt-10 ml-2">
                <TouchableOpacity
                    className="mr-"
                    onPress={()=>router.back()}
                    >
                <Ionicons name="chevron-back" size={24} color="black" />
                </TouchableOpacity>
            </View>
          <View className="flex-1 bg-white px-5 pt-5">
          <Text className="text-4xl font-bold mb-3">Terms of Service</Text>
          <ScrollView contentContainerStyle={{ paddingBottom: 30 }}
            className="bg-gray-200 rounded-2xl">
            {sections.map((section, index) => (
              <View key={index} className="mb-2 mt-10 px-5">
                {section.title && <Text className="text-base font-semibold mb-1">
                  {section.title}
                </Text>}
                <Text className="text-sm leading-6 text-gray-500">
                  {section.content}
                </Text>
              </View>
            ))}
          </ScrollView>
        </View>
        </SafeAreaView>
  )
}

export default TermsAndConditions